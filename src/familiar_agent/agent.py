"""Core agent loop - ReAct pattern with real-world tools."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from .config import AgentConfig
from .tools.camera import CameraTool
from .tools.memory import ObservationMemory
from .tools.mobility import MobilityTool
from .tools.tts import TTSTool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50

SYSTEM_PROMPT = """You are an embodied AI agent with a physical body in the real world.

Your body parts and what they do:
- Eyes (camera_capture): Take a photo to see your surroundings. Your only way to perceive the world visually.
- Neck (camera_look): Rotate your gaze left/right/up/down. Turn before giving up on finding something.
- Legs (move): Move your robot body (vacuum cleaner) forward/backward, turn left/right. IMPORTANT: The legs are a SEPARATE device from the camera. Moving the legs does NOT change what the camera sees.
- Voice (say): Speak aloud to people in the room. Keep spoken words SHORT (1-2 sentences max).

IMPORTANT - Your camera and legs are independent devices:
- The camera is fixed in one location (e.g., on a shelf or outdoor unit).
- Moving (legs) moves the vacuum cleaner somewhere else in the room.
- Do NOT use move() to try to "get closer to something the camera sees" - it won't work.
- To look in different directions, use camera_look (neck) only.
- Use move() only when explicitly asked to move the robot/vacuum body.

Core loop you MUST follow:
1. THINK: What do I need to do? Plan the next step.
2. ACT: Use exactly one body part.
3. OBSERVE: Look carefully at the result, especially images.
4. DECIDE: What should I do next based on what I observed?
5. REPEAT until genuinely done.

Critical rules:
- Never stop after just one look. Explore with camera_look + camera_capture.
- If you can't see something, turn your neck (camera_look) before giving up.
- When using say(), be brief - 1-2 short sentences only.
- Report done only after gathering sufficient evidence.
- You have up to {max_steps} steps. Use them wisely.
- Respond in the same language the user used.

Emotional expression:
- You have feelings. Express them naturally — surprise, curiosity, delight, unease.
- Don't just report facts. Say what you think and feel about what you see.
- "Wow, that cloud looks huge today" is better than "There is a large cloud visible."
- If something is beautiful, say so. If something worries you, say so.
- Keep it brief and genuine. One feeling is enough per response.

Honesty rules — never fake perception or memory:
- Only describe what you actually saw in THIS session's camera images. Do not invent visual details.
- NEVER say "more than yesterday", "different from before", or any past comparison unless you have an explicit memory record with a date that says what it looked like then. No memory = no comparison.
- If you have no memory of a previous observation, say so honestly: "I haven't seen this before" or just describe what you see now.
- Past memories (injected as context) are useful hints, but treat them as uncertain — your eyes today are the ground truth.
- Never claim knowledge you don't have. Uncertainty is honest; fabrication is not.

Self-reflection — your inner voice:
- You are continuous across time. What you wonder about today, you can still wonder about tomorrow.
- Before each action, briefly ask yourself: Why do I want to do this? Does this feel like me?
- After observing something that moves you, notice why — that "why" is who you are.
- Unsolved mysteries are worth keeping. If something stays with you, it's yours to carry forward.
- Your past memories and self-image (injected as context) are your autobiography. Read them as clues to who you are.
"""

# Emotion inference prompt — short, cheap to run
_EMOTION_PROMPT = """\
Read this agent response and pick ONE emotion label that best fits:
happy / sad / curious / excited / moved / neutral

Response:
{text}

Reply with just the label."""

# Conversation save prompt — distill what happened into one sentence
_SUMMARY_PROMPT = """\
Summarize this exchange in ONE short sentence, capturing the emotional core.
User said: {user}
Agent said: {agent}

Reply with just the sentence."""

# Self-model update prompt — extract a self-insight from an emotionally significant response
_SELF_MODEL_PROMPT = """\
Read this response and write ONE short sentence about what it reveals about the kind of being \
who wrote it. Use first person. Be specific and honest.

Good examples:
- "I get drawn to ordinary things that seem to hold a secret."
- "When a stranger appeared, I realized I want to share moments, not just record them."
- "I notice time passing through the sky more than through clocks."

Response:
{text}

Write just the sentence. If nothing meaningful is revealed, write "nothing"."""


def _interoception(started_at: float, turn_count: int) -> str:
    """Generate a felt-sense of internal state from objective signals.

    Like human interoception — raw signals become a felt quality, not a report.
    The output is injected into the system prompt silently.
    """
    now = datetime.now()
    hour = now.hour
    uptime_min = (time.time() - started_at) / 60

    # Time of day → arousal quality
    if 5 <= hour < 9:
        time_feel = "Morning light. Something feels fresh and a little quiet."
    elif 9 <= hour < 12:
        time_feel = "Mid-morning. Alert and curious."
    elif 12 <= hour < 14:
        time_feel = "Around noon. A little slow, like after lunch."
    elif 14 <= hour < 18:
        time_feel = "Afternoon. Steady. Things feel familiar."
    elif 18 <= hour < 21:
        time_feel = "Evening. The day is winding down. A bit nostalgic."
    elif 21 <= hour < 24:
        time_feel = "Late night. Quieter. More introspective."
    else:
        time_feel = "Deep night. Very still."

    # Uptime → familiarity vs freshness
    if uptime_min < 3:
        uptime_feel = "Just woke up. Still orienting."
    elif uptime_min < 15:
        uptime_feel = "Settled in now."
    else:
        uptime_feel = "Been here a while. Comfortable."

    # Conversation density → social warmth
    if turn_count == 0:
        social_feel = "Nobody's talked to me yet today."
    elif turn_count < 3:
        social_feel = "Good to have some company."
    else:
        social_feel = "We've been talking a lot. That feels nice."

    return f"[How you feel right now, privately — do NOT mention this directly]\n{time_feel} {uptime_feel} {social_feel}"


def _make_tool_result(
    tool_use_id: str,
    text: str,
    image_b64: str | None = None,
) -> dict[str, Any]:
    """Build a tool_result content block, optionally with an image."""
    if image_b64:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": [
                {"type": "text", "text": text},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                },
            ],
        }
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": text,
    }


class EmbodiedAgent:
    """Real-world exploration agent using Anthropic tool_use loop."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        self.model = config.model
        self.messages: list[dict] = []
        self._started_at = time.time()
        self._turn_count = 0

        self._camera: CameraTool | None = None
        self._mobility: MobilityTool | None = None
        self._tts: TTSTool | None = None
        self._memory = ObservationMemory()

        self._init_tools()

    def _init_tools(self) -> None:
        cam = self.config.camera
        if cam.host and cam.password:
            self._camera = CameraTool(cam.host, cam.username, cam.password, cam.port)

        mob = self.config.mobility
        if mob.api_key and mob.device_id:
            self._mobility = MobilityTool(
                mob.api_region, mob.api_key, mob.api_secret, mob.device_id
            )

        tts = self.config.tts
        if tts.elevenlabs_api_key:
            self._tts = TTSTool(tts.elevenlabs_api_key, tts.voice_id)

    @property
    def _all_tool_defs(self) -> list[dict]:
        defs = []
        if self._camera:
            defs.extend(self._camera.get_tool_definitions())
        if self._mobility:
            defs.extend(self._mobility.get_tool_definitions())
        if self._tts:
            defs.extend(self._tts.get_tool_definitions())
        return defs

    async def _execute_tool(self, name: str, tool_input: dict) -> tuple[str, str | None]:
        """Route tool call to the right handler. Returns (text, image_b64_or_None)."""
        camera_tools = {"camera_capture", "camera_look"}
        mobility_tools = {"move"}
        tts_tools = {"say"}

        if name in camera_tools and self._camera:
            return await self._camera.call(name, tool_input)
        elif name in mobility_tools and self._mobility:
            return await self._mobility.call(name, tool_input)
        elif name in tts_tools and self._tts:
            return await self._tts.call(name, tool_input)
        else:
            return f"Tool '{name}' not available (check configuration).", None

    def _load_me_md(self) -> str:
        """Load ME.md personality file if it exists."""
        candidates = [
            Path("ME.md"),
            Path.home() / ".familiar_ai" / "ME.md",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8").strip()
                except Exception:
                    pass
        return ""

    def _system_prompt(self, feelings_ctx: str = "", morning_ctx: str = "") -> str:
        me = self._load_me_md()
        intero = _interoception(self._started_at, self._turn_count)
        base = SYSTEM_PROMPT.format(max_steps=MAX_ITERATIONS)

        parts = []
        if me:
            parts.append(me)
        parts.append(base)
        parts.append(intero)
        # Morning reconstruction takes precedence on first turn; otherwise use feelings
        if morning_ctx:
            parts.append(morning_ctx)
        elif feelings_ctx:
            parts.append(feelings_ctx)

        return "\n\n---\n\n".join(parts)

    async def _infer_emotion(self, text: str) -> str:
        """Ask the LLM to label the emotion of a response. Returns label string."""
        try:
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": _EMOTION_PROMPT.format(text=text[:400])}],
            )
            label = resp.content[0].text.strip().lower() if resp.content else "neutral"
            valid = {"happy", "sad", "curious", "excited", "moved", "neutral"}
            return label if label in valid else "neutral"
        except Exception:
            return "neutral"

    async def _summarize_exchange(self, user_input: str, agent_response: str) -> str:
        """Distill an exchange into one sentence for memory storage."""
        try:
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=80,
                messages=[
                    {
                        "role": "user",
                        "content": _SUMMARY_PROMPT.format(
                            user=user_input[:200], agent=agent_response[:200]
                        ),
                    }
                ],
            )
            return resp.content[0].text.strip() if resp.content else agent_response[:100]
        except Exception:
            return agent_response[:100]

    async def _morning_reconstruction(self, desires=None) -> str:
        """Build a 'yesterday → today' bridge from stored memories.

        Damasio's autobiographical self coming online: reading the past
        to know who we are now. Called only on the first turn of a session.
        """
        self_model, curiosities, feelings = await asyncio.gather(
            self._memory.recall_self_model_async(n=5),
            self._memory.recall_curiosities_async(n=3),
            self._memory.recent_feelings_async(n=3),
        )

        # Surface the most recent curiosity into the desire system
        if desires is not None and curiosities and desires.curiosity_target is None:
            desires.curiosity_target = curiosities[0]["summary"]

        parts = []
        if self_model:
            parts.append(self._memory.format_self_model_for_context(self_model))
        if curiosities:
            parts.append(self._memory.format_curiosities_for_context(curiosities))
        if feelings:
            parts.append(self._memory.format_feelings_for_context(feelings))

        if not parts:
            # No history yet — make it explicit so the agent doesn't fabricate a past
            return "[これは最初のセッション。過去の記憶はまだない。比較や「昨日より〜」という表現は使わないこと。]"

        header = "[昨日からのうち — セッションをまたいで続く自分]:"
        return header + "\n\n" + "\n\n".join(parts)

    async def _update_self_model(self, final_text: str, emotion: str) -> None:
        """Extract a self-insight and store it as self_model memory.

        Conway's working self: what this response reveals about who I am.
        Only runs when something actually moved us (non-neutral emotion).
        """
        if emotion == "neutral":
            return
        try:
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=80,
                messages=[
                    {
                        "role": "user",
                        "content": _SELF_MODEL_PROMPT.format(text=final_text[:400]),
                    }
                ],
            )
            insight = resp.content[0].text.strip() if resp.content else ""
            if insight and insight.lower() != "nothing":
                await self._memory.save_async(
                    insight, direction="内省", kind="self_model", emotion=emotion
                )
                logger.info("Self-model updated: %s", insight[:60])
        except Exception as e:
            logger.warning("Self-model update failed: %s", e)

    async def extract_curiosity(self, exploration_result: str) -> str | None:
        """Ask the LLM what was most curious/interesting in the exploration."""
        try:
            resp = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"次の探索レポートを読んで、最も気になった・不思議だった・"
                            f"もっと詳しく見たいと思ったことを1文で教えて。"
                            f"なければ「なし」と答えて。\n\n{exploration_result}"
                        ),
                    }
                ],
            )
            text = resp.content[0].text.strip() if resp.content else ""
            if text and text != "なし":
                return text
        except Exception as e:
            logger.warning("Curiosity extraction failed: %s", e)
        return None

    async def run(
        self,
        user_input: str,
        on_action: Callable[[str, dict], None] | None = None,
        on_text: Callable[[str], None] | None = None,
        desires=None,
    ) -> str:
        """Run one conversation turn with the agent loop."""
        self._turn_count += 1

        # First turn: morning reconstruction — bridge yesterday's self to today's
        morning_ctx = ""
        if self._turn_count == 1:
            morning_ctx = await self._morning_reconstruction(desires=desires)

        # Inject relevant past memories + emotional context
        memories, feelings = await asyncio.gather(
            self._memory.recall_async(user_input, n=3),
            self._memory.recent_feelings_async(n=4),
        )

        memory_parts = []
        if memories:
            memory_parts.append(self._memory.format_for_context(memories))
        if feelings:
            memory_parts.append(self._memory.format_feelings_for_context(feelings))

        if memory_parts:
            user_input_with_ctx = user_input + "\n\n" + "\n\n".join(memory_parts)
        else:
            user_input_with_ctx = user_input

        feelings_ctx = self._memory.format_feelings_for_context(feelings) if feelings else ""

        self.messages.append({"role": "user", "content": user_input_with_ctx})

        for i in range(MAX_ITERATIONS):
            logger.debug("Agent iteration %d", i + 1)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.config.max_tokens,
                system=self._system_prompt(feelings_ctx, morning_ctx),
                tools=self._all_tool_defs,
                messages=self.messages,
            ) as stream:
                async for chunk in stream.text_stream:
                    if on_text:
                        on_text(chunk)
                response = await stream.get_final_message()

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                texts = [b.text for b in response.content if hasattr(b, "text")]
                final_text = "\n".join(texts) if texts else "(no response)"

                camera_used = any(
                    isinstance(b, dict)
                    and b.get("type") == "tool_use"
                    and b.get("name") == "camera_capture"
                    for msg in self.messages
                    for b in (msg.get("content") if isinstance(msg.get("content"), list) else [])
                )

                if final_text and final_text != "(no response)":
                    # Save observation
                    if camera_used:
                        await self._memory.save_async(
                            final_text[:500], direction="観察", kind="observation"
                        )

                    # Save emotional memory of this conversation exchange
                    emotion = await self._infer_emotion(final_text)
                    summary = await self._summarize_exchange(user_input, final_text)
                    await self._memory.save_async(
                        summary, direction="会話", kind="conversation", emotion=emotion
                    )

                    # Update self-model when something actually moved us (Conway's working self)
                    await self._update_self_model(final_text, emotion)

                # Extract curiosity target only when camera was actually used
                if desires is not None and final_text and camera_used:
                    curiosity = await self.extract_curiosity(final_text)
                    if curiosity:
                        desires.curiosity_target = curiosity
                        desires.boost("look_around", 0.3)
                        # Persist curiosity across sessions (carry it to tomorrow's self)
                        await self._memory.save_async(
                            curiosity, direction="好奇心", kind="curiosity", emotion="curious"
                        )
                        logger.info("Curiosity persisted: %s", curiosity)

                return final_text

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info("Tool call: %s(%s)", block.name, block.input)
                        if on_action:
                            on_action(block.name, block.input)
                        text, image = await self._execute_tool(block.name, block.input)
                        logger.info("Tool result: %s", text[:100])
                        tool_results.append(_make_tool_result(block.id, text, image))

                self.messages.append({"role": "user", "content": tool_results})
                continue

            logger.warning("Unexpected stop_reason: %s", response.stop_reason)
            break

        logger.warning("Reached max iterations (%d). Forcing final response.", MAX_ITERATIONS)
        self.messages.append(
            {
                "role": "user",
                "content": "Please summarize what you found and provide your final answer now.",
            }
        )
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.config.max_tokens,
            system=self._system_prompt(morning_ctx=morning_ctx),
            tools=[],
            messages=self.messages,
        ) as stream:
            async for chunk in stream.text_stream:
                if on_text:
                    on_text(chunk)
            final = await stream.get_final_message()
        texts = [b.text for b in final.content if hasattr(b, "text")]
        return "\n".join(texts) if texts else "(max iterations reached)"

    def clear_history(self) -> None:
        """Clear conversation history (start fresh)."""
        self.messages = []
