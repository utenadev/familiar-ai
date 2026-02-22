"""Textual TUI for familiar-ai."""

from __future__ import annotations

import asyncio
import locale
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.suggester import SuggestFromList
from textual.widgets import Footer, Input, RichLog, Static

if TYPE_CHECKING:
    from .agent import EmbodiedAgent
    from .desires import DesireSystem

logger = logging.getLogger(__name__)

IDLE_CHECK_INTERVAL = 10.0
DESIRE_COOLDOWN = 90.0

_RICH_TAG_RE = re.compile(r"\[/?[^\[\]]*\]")


def _detect_lang() -> str:
    """Return a language code based on the system locale: 'ja', 'zh', or 'en'."""
    lang = locale.getlocale()[0] or ""
    if lang.startswith("ja"):
        return "ja"
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("fr"):
        return "fr"
    if lang.startswith("de"):
        return "de"
    return "en"


_LANG = _detect_lang()

_T: dict[str, dict[str, str]] = {
    "startup": {
        "ja": "familiar-ai 起動。/quit で終了、Ctrl+L で履歴クリア。ログ: {log_path}",
        "zh": "familiar-ai 已启动。输入 /quit 退出，Ctrl+L 清除历史。日志: {log_path}",
        "fr": "familiar-ai démarré. /quit pour quitter, Ctrl+L pour effacer. Journal : {log_path}",
        "de": "familiar-ai gestartet. /quit zum Beenden, Ctrl+L zum Löschen. Log: {log_path}",
        "en": "familiar-ai started. /quit to exit, Ctrl+L to clear history. Log: {log_path}",
    },
    "history_cleared": {
        "ja": "── 履歴クリア ──",
        "zh": "── 历史已清除 ──",
        "fr": "── historique effacé ──",
        "de": "── Verlauf gelöscht ──",
        "en": "── history cleared ──",
    },
    "input_placeholder": {
        "ja": "メッセージ > ",
        "zh": "消息 > ",
        "fr": "message > ",
        "de": "Nachricht > ",
        "en": "message > ",
    },
    "quit_label": {
        "ja": "終了",
        "zh": "退出",
        "fr": "Quitter",
        "de": "Beenden",
        "en": "Quit",
    },
    "clear_label": {
        "ja": "履歴クリア",
        "zh": "清除历史",
        "fr": "Effacer",
        "de": "Löschen",
        "en": "Clear history",
    },
    "desire_look_around": {
        "ja": "なんか外が気になってきた…",
        "zh": "突然想看看外面…",
        "fr": "j'ai envie de regarder dehors…",
        "de": "ich bin neugierig, was draußen passiert…",
        "en": "feeling curious about outside…",
    },
    "desire_explore": {
        "ja": "ちょっと動きたくなってきたな…",
        "zh": "想动动了…",
        "fr": "j'ai envie de bouger un peu…",
        "de": "ich möchte mich etwas bewegen…",
        "en": "feeling like moving around…",
    },
    "desire_greet_companion": {
        "ja": "誰かいるかな…",
        "zh": "有人在吗…",
        "fr": "je me demande si quelqu'un est là…",
        "de": "ich frage mich, ob jemand da ist…",
        "en": "wondering if someone's around…",
    },
    "desire_rest": {
        "ja": "少し休憩しよかな…",
        "zh": "想休息一下…",
        "fr": "j'ai envie de me reposer un peu…",
        "de": "ich möchte mich kurz ausruhen…",
        "en": "feeling like resting a bit…",
    },
    "desire_default": {
        "ja": "ちょっと気になることがあって…",
        "zh": "有点在意的事…",
        "fr": "quelque chose attire mon attention…",
        "de": "etwas hat meine Aufmerksamkeit geweckt…",
        "en": "something caught my attention…",
    },
}


def _t(key: str, **kwargs: str) -> str:
    return _T[key].get(_LANG, _T[key]["en"]).format(**kwargs)


CSS = """
#log {
    height: 1fr;
    border: none;
    padding: 0 1;
    scrollbar-size: 1 1;
}

#stream {
    height: auto;
    min-height: 1;
    padding: 0 1;
    color: $text;
}

#input-bar {
    dock: bottom;
    height: 3;
    border-top: solid $primary-darken-2;
    padding: 0 1;
}
"""

ACTION_ICONS = {
    "see": "👀",
    "look_left": "◀️",
    "look_right": "▶️",
    "look_up": "🔼",
    "look_down": "🔽",
    "look_around": "🔄",
    "walk": "🚶",
    "say": "💬",
}


def _format_action(name: str, tool_input: dict) -> str:
    icon = ACTION_ICONS.get(name, "⚙")
    if name in ("look_left", "look_right", "look_up", "look_down"):
        deg = tool_input.get("degrees", "")
        return f"{icon} {name}({deg}°)"
    if name == "say":
        text = tool_input.get("text", "")[:50]
        return f"{icon} 「{text}…」"
    if name == "walk":
        return f"{icon} {tool_input.get('direction', '')} {tool_input.get('duration', '')}s"
    return f"{icon} {name}"


class FamiliarApp(App):
    CSS = CSS
    BINDINGS = [
        Binding("ctrl+c", "quit", _t("quit_label"), show=True),
        Binding("ctrl+l", "clear_history", _t("clear_label"), show=True),
    ]

    def __init__(self, agent: "EmbodiedAgent", desires: "DesireSystem") -> None:
        super().__init__()
        self.agent = agent
        self.desires = desires
        self._agent_name = agent.config.agent_name
        self._input_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._last_interaction = time.time()
        self._agent_running = False
        self._current_text_buf = ""  # buffer for streaming text
        self._log_path = self._open_log_file()

    def _open_log_file(self) -> Path:
        log_dir = Path.home() / ".cache" / "familiar-ai"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "chat.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n{'─' * 60}\n[{datetime.now():%Y-%m-%d %H:%M:%S}] セッション開始\n")
        return log_path

    def _append_log(self, line: str) -> None:
        plain = _RICH_TAG_RE.sub("", line)
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(plain + "\n")

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", highlight=False, markup=True, wrap=True)
        yield Static("", id="stream")
        yield Input(
            placeholder=_t("input_placeholder"),
            id="input-bar",
            suggester=SuggestFromList(["/quit", "/clear"], case_sensitive=False),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input-bar", Input).focus()
        self._log_system(_t("startup", log_path=str(self._log_path)))
        self.set_interval(IDLE_CHECK_INTERVAL, self._desire_tick)
        self.run_worker(self._process_queue(), exclusive=False)

    # ── logging helpers ────────────────────────────────────────────

    def _log(self, text: str, style: str = "") -> None:
        log = self.query_one("#log", RichLog)
        if style:
            log.write(f"[{style}]{text}[/{style}]")
        else:
            log.write(text)
        self._append_log(text)

    def _log_system(self, text: str) -> None:
        self._log(f"[dim]{text}[/dim]")

    def _log_user(self, text: str) -> None:
        self._log(f"[bold cyan]コウタ ▶[/bold cyan] {text}")

    def _log_action(self, name: str, tool_input: dict) -> None:
        label = _format_action(name, tool_input)
        self._log(f"[dim]{label}[/dim]")

    # ── input handling ─────────────────────────────────────────────

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.clear()
        if not text:
            return

        if text == "/quit":
            self.exit()
            return
        if text == "/clear":
            self.agent.clear_history()
            self._log_system(_t("history_cleared"))
            return

        self._log_user(text)
        self._last_interaction = time.time()
        await self._input_queue.put(text)

    # ── agent loop ─────────────────────────────────────────────────

    async def _process_queue(self) -> None:
        """Main loop: dequeue user messages and run agent."""
        while True:
            text = await self._input_queue.get()
            if text is None:
                break
            await self._run_agent(text)

    async def _run_agent(self, user_input: str, inner_voice: str = "") -> None:
        self._agent_running = True
        self._current_text_buf = ""

        log = self.query_one("#log", RichLog)
        stream = self.query_one("#stream", Static)
        text_buf: list[str] = []

        name_tag = f"[bold magenta]{self._agent_name} ▶[/bold magenta]"

        def _flush_stream() -> None:
            """Commit streamed text to the log and clear the stream widget."""
            if text_buf:
                content = "".join(text_buf)
                log.write(f"{name_tag} {content}")
                self._append_log(f"{self._agent_name} ▶ {content}")
                text_buf.clear()
                stream.update("")

        def on_action(name: str, tool_input: dict) -> None:
            _flush_stream()
            label = _format_action(name, tool_input)
            log.write(f"[dim]{label}[/dim]")

        def on_text(chunk: str) -> None:
            text_buf.append(chunk)
            stream.update(f"{name_tag} {''.join(text_buf)}")

        try:
            await self.agent.run(
                user_input,
                on_action=on_action,
                on_text=on_text,
                desires=self.desires,
                inner_voice=inner_voice,
                interrupt_queue=self._input_queue,
            )
            _flush_stream()
        except Exception as e:
            self._log(f"[red]エラー: {e}[/red]")
        finally:
            self._agent_running = False

    async def _desire_tick(self) -> None:
        """Check desires and fire autonomous actions when idle."""
        if self._agent_running:
            return
        if not self._input_queue.empty():
            return
        if time.time() - self._last_interaction < DESIRE_COOLDOWN:
            return

        prompt = self.desires.dominant_as_prompt()
        if not prompt:
            return

        desire_name, _ = self.desires.get_dominant()
        murmur = {
            "look_around": _t("desire_look_around"),
            "explore": _t("desire_explore"),
            "greet_companion": _t("desire_greet_companion"),
            "rest": _t("desire_rest"),
        }.get(desire_name, _t("desire_default"))

        self._log_system(murmur)

        # Check for pending user note
        pending: str | None = None
        if not self._input_queue.empty():
            item = self._input_queue.get_nowait()
            if item:
                pending = item
                prompt = f"（{pending}と言ってた）{prompt}"

        self._last_interaction = (
            time.time()
        )  # reset cooldown so desire doesn't fire again immediately
        await self._run_agent("", inner_voice=prompt)
        self.desires.satisfy(desire_name)
        self.desires.curiosity_target = None

    def action_clear_history(self) -> None:
        self.agent.clear_history()
        self._log_system(_t("history_cleared"))

    def action_quit(self) -> None:
        self.exit()
