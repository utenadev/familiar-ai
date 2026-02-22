"""TTS tool - voice of the embodied agent."""

from __future__ import annotations

import logging
import tempfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are speaking aloud. Keep responses concise when using this tool."""


class TTSTool:
    """Text-to-speech using ElevenLabs."""

    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    async def say(self, text: str) -> str:
        """Speak text aloud via ElevenLabs. Truncate to 200 chars for speed."""
        import aiohttp
        import asyncio

        # Truncate long texts - spoken words should be brief
        if len(text) > 200:
            text = text[:197] + "..."

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    return f"TTS failed: {resp.status}"
                audio_data = await resp.read()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            tmp_path = f.name

        # Try mpv first; fall back to ffplay if mpv fails
        for player_args in (
            ["mpv", "--no-terminal", "--ao=pulse", tmp_path],
            ["mpv", "--no-terminal", tmp_path],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", tmp_path],
        ):
            proc = await asyncio.create_subprocess_exec(
                *player_args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode == 0:
                return f"Said: {text[:50]}..."
            err = stderr.decode(errors="replace").strip()
            logger.warning("%s failed (exit %d): %s", player_args[0], proc.returncode, err[:120])

        return "TTS playback failed (mpv and ffplay both failed)"

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "name": "say",
                "description": "Speak text aloud. Use to communicate with people in the room.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to speak. Can include ElevenLabs audio tags like [cheerful], [warmly].",
                        }
                    },
                    "required": ["text"],
                },
            },
        ]

    async def call(self, tool_name: str, tool_input: dict) -> tuple[str, None]:
        if tool_name == "say":
            result = await self.say(tool_input["text"])
            return result, None
        return f"Unknown tool: {tool_name}", None
