"""File management tool - allows the agent to read and write in a safe workspace."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Base directory for AI operations - ensures safety
WORKSPACE_DIR = Path.cwd() / "workspace"
# Disallowed filenames/patterns to protect secrets and system integrity
DENYLIST = {
    ".env", "ME.md", ".git", ".venv", "__pycache__", 
    ".python-version", "uv.lock", "pyproject.toml"
}

class FileTool:
    """Provides safe file I/O within a restricted workspace directory."""

    def __init__(self, base_dir: Path | str = WORKSPACE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("FileTool initialized. Workspace: %s", self.base_dir)

    def _safe_path(self, relative_path: str) -> Path | None:
        """Resolve and validate a path to ensure it's inside the workspace and not denylisted."""
        try:
            # Prevent absolute paths or ".." from escaping workspace
            target = (self.base_dir / relative_path).resolve()
            if not target.is_relative_to(self.base_dir):
                logger.warning("Access denied: Path '%s' is outside workspace.", relative_path)
                return None
            
            # Check against denylist (parts of the path)
            for part in target.parts:
                if part in DENYLIST:
                    logger.warning("Access denied: Path '%s' contains restricted part '%s'.", relative_path, part)
                    return None
            
            return target
        except Exception as e:
            logger.error("Path resolution failed for '%s': %s", relative_path, e)
            return None

    def list_files(self, sub_dir: str = ".") -> str:
        """List files in the workspace (or a subdirectory)."""
        target = self._safe_path(sub_dir)
        if not target or not target.is_dir():
            return "Error: Directory not found or access denied."
        
        try:
            items = os.listdir(target)
            if not items:
                return "Directory is empty."
            return "
".join(f"- {item}" for item in items if item not in DENYLIST)
        except Exception as e:
            return f"Error listing files: {e}"

    def read_file(self, filename: str, max_lines: int = 100) -> str:
        """Read text from a file (limited to max_lines)."""
        target = self._safe_path(filename)
        if not target or not target.is_file():
            return f"Error: File '{filename}' not found or access denied."
        
        try:
            lines = []
            with target.open("r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"
--- [Truncated: File is longer than {max_lines} lines] ---")
                        break
                    lines.append(line.rstrip())
            
            content = "
".join(lines)
            return content if content else "(Empty file)"
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, filename: str, content: str) -> str:
        """Write text to a file in the workspace."""
        target = self._safe_path(filename)
        if not target:
            return "Error: Access denied or invalid path."
        
        try:
            # Ensure parent directories exist
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            logger.info("File written: %s", filename)
            return f"Successfully wrote to {filename}."
        except Exception as e:
            logger.error("Write failed to '%s': %s", filename, e)
            return f"Error writing file: {e}"

    def see_file(self, filename: str) -> tuple[str, str | None]:
        """Read an image file and return it as base64 for vision processing."""
        target = self._safe_path(filename)
        if not target or not target.is_file():
            return f"Error: Image file '{filename}' not found or access denied.", None
        
        ext = target.suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            return f"Error: File '{filename}' is not a supported image format.", None

        try:
            data = target.read_bytes()
            b64 = base64.b64encode(data).decode()
            return f"You are looking at the file: {filename}", b64
        except Exception as e:
            logger.error("Failed to read image file '%s': %s", filename, e)
            return f"Error reading image file: {e}", None

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "name": "list_files",
                "description": "List files in your workspace directory.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sub_dir": {
                            "type": "string",
                            "description": "Optional subdirectory to list",
                            "default": "."
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read text content from a file in your workspace.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Name of the file to read"},
                        "max_lines": {
                            "type": "integer", 
                            "description": "Maximum lines to read (default 100)",
                            "default": 100
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "write_file",
                "description": "Write or overwrite a text file in your workspace. Use this to save notes, logs, or your thoughts.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Name of the file to write"},
                        "content": {"type": "string", "description": "Text content to save"}
                    },
                    "required": ["filename", "content"]
                }
            },
            {
                "name": "see_file",
                "description": "Open and see an image file (JPEG, PNG, WebP) in your workspace using your vision.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Name of the image file to see"}
                    },
                    "required": ["filename"]
                }
            }
        ]

    async def call(self, tool_name: str, tool_input: dict) -> tuple[str, str | None]:
        if tool_name == "list_files":
            res = self.list_files(tool_input.get("sub_dir", "."))
            return res, None
        elif tool_name == "read_file":
            res = self.read_file(tool_input["filename"], tool_input.get("max_lines", 100))
            return res, None
        elif tool_name == "write_file":
            res = self.write_file(tool_input["filename"], tool_input["content"])
            return res, None
        elif tool_name == "see_file":
            return self.see_file(tool_input["filename"])
        return f"Unknown tool: {tool_name}", None
