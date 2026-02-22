"""Observation memory - SQLite + multilingual-e5-small embeddings.

Architecture inspired by memory-mcp (Phase 11: SQLite+numpy).
- Fast startup: no heavy DB server
- Semantic search: multilingual-e5-small (~117MB, lazy loaded)
- Hybrid: vector similarity + LIKE keyword fallback
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

DB_PATH = str(Path.home() / ".familiar_ai" / "observations.db")
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

_DDL = """
CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'unknown'
);
CREATE INDEX IF NOT EXISTS idx_obs_timestamp ON observations(timestamp);
CREATE INDEX IF NOT EXISTS idx_obs_date ON observations(date);

CREATE TABLE IF NOT EXISTS obs_embeddings (
    obs_id TEXT PRIMARY KEY REFERENCES observations(id) ON DELETE CASCADE,
    vector BLOB NOT NULL
);
"""

# ── vector helpers (same as memory-mcp) ──────────────────────

def _cosine_similarity(query: np.ndarray, corpus: np.ndarray) -> np.ndarray:
    q_norm = query / (np.linalg.norm(query) + 1e-10)
    c_norm = corpus / (np.linalg.norm(corpus, axis=1, keepdims=True) + 1e-10)
    return c_norm @ q_norm

def _encode_vector(vec: list[float]) -> bytes:
    return np.array(vec, dtype=np.float32).tobytes()

def _decode_vector(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


# ── lazy embedding model ──────────────────────────────────────

class _EmbeddingModel:
    """Lazy-loaded multilingual-e5-small."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self._model_name = model_name
        self._model: Any = None

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model %s...", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded.")

    def encode_document(self, texts: list[str]) -> list[list[float]]:
        self._load()
        prefixed = [f"passage: {t}" for t in texts]
        return self._model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False).tolist()

    def encode_query(self, texts: list[str]) -> list[list[float]]:
        self._load()
        prefixed = [f"query: {t}" for t in texts]
        return self._model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False).tolist()


# ── ObservationMemory ─────────────────────────────────────────

class ObservationMemory:
    """SQLite + vector embedding observation memory."""

    def __init__(self, db_path: str = DB_PATH, model_name: str = EMBEDDING_MODEL):
        self._db_path = db_path
        self._db: sqlite3.Connection | None = None
        self._embedder = _EmbeddingModel(model_name)

    def _ensure_connected(self) -> sqlite3.Connection:
        if self._db is None:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self._db_path, check_same_thread=False)
            self._db.row_factory = sqlite3.Row
            self._db.execute("PRAGMA journal_mode = WAL")
            self._db.execute("PRAGMA synchronous = NORMAL")
            self._db.execute("PRAGMA foreign_keys = ON")
            for stmt in _DDL.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    self._db.execute(stmt)
            self._db.commit()
        return self._db

    def save(self, content: str, direction: str = "unknown") -> bool:
        """Save observation with embedding synchronously."""
        try:
            db = self._ensure_connected()
            now = datetime.now()
            obs_id = str(uuid.uuid4())

            # Embed the content
            vec = self._embedder.encode_document([content])[0]
            blob = _encode_vector(vec)

            db.execute(
                "INSERT INTO observations (id, content, timestamp, date, time, direction) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (obs_id, content, now.isoformat(),
                 now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), direction),
            )
            db.execute(
                "INSERT INTO obs_embeddings (obs_id, vector) VALUES (?, ?)",
                (obs_id, blob),
            )
            db.commit()
            logger.info("Saved observation: %s...", content[:60])
            return True
        except Exception as e:
            logger.warning("Failed to save observation: %s", e)
            return False

    def recall(self, query: str, n: int = 3) -> list[dict]:
        """Recall by vector similarity. Fallback to LIKE + recency."""
        try:
            db = self._ensure_connected()

            # Check if we have embeddings
            count = db.execute("SELECT COUNT(*) FROM obs_embeddings").fetchone()[0]

            if count > 0:
                # Vector search
                query_vec = np.array(self._embedder.encode_query([query])[0], dtype=np.float32)

                rows = db.execute(
                    "SELECT o.id, o.content, o.date, o.time, o.direction, e.vector "
                    "FROM observations o JOIN obs_embeddings e ON o.id = e.obs_id"
                ).fetchall()

                vecs = np.stack([_decode_vector(bytes(r["vector"])) for r in rows])
                scores = _cosine_similarity(query_vec, vecs)

                # Top-n by similarity
                top_indices = np.argsort(scores)[::-1][:n]
                return [
                    {
                        "summary": rows[i]["content"],
                        "date": rows[i]["date"],
                        "time": rows[i]["time"],
                        "direction": rows[i]["direction"],
                        "score": float(scores[i]),
                    }
                    for i in top_indices
                ]

            # Fallback: LIKE keyword search + recency
            keywords = [w for w in query.split() if len(w) > 1][:4]
            if keywords:
                conditions = " OR ".join("content LIKE ?" for _ in keywords)
                params = [f"%{kw}%" for kw in keywords] + [n]
                rows = db.execute(
                    f"SELECT content, date, time, direction FROM observations "
                    f"WHERE {conditions} ORDER BY timestamp DESC LIMIT ?",
                    params,
                ).fetchall()
                if rows:
                    return [{"summary": r["content"], "date": r["date"],
                             "time": r["time"], "direction": r["direction"]} for r in rows]

            # Last resort: most recent
            rows = db.execute(
                "SELECT content, date, time, direction FROM observations "
                "ORDER BY timestamp DESC LIMIT ?", (n,)
            ).fetchall()
            return [{"summary": r["content"], "date": r["date"],
                     "time": r["time"], "direction": r["direction"]} for r in rows]

        except Exception as e:
            logger.warning("Failed to recall observations: %s", e)
            return []

    def format_for_context(self, memories: list[dict]) -> str:
        if not memories:
            return ""
        lines = ["[過去の観察記憶]:"]
        for m in memories:
            score_str = f" (類似度:{m['score']:.2f})" if "score" in m else ""
            lines.append(
                f"- {m['date']} {m['time']} ({m['direction']}方向){score_str}: {m['summary'][:120]}"
            )
        return "\n".join(lines)

    async def save_async(self, content: str, direction: str = "unknown") -> bool:
        return await asyncio.to_thread(self.save, content, direction)

    async def recall_async(self, query: str, n: int = 3) -> list[dict]:
        return await asyncio.to_thread(self.recall, query, n)
