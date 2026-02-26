import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from familiar_agent.agent import EmbodiedAgent
from familiar_agent.config import AgentConfig

@pytest.fixture
def mock_config():
    config = AgentConfig()
    config.api_key = "fake-key"
    config.camera.host = ""
    return config

@pytest.fixture
def mock_memory():
    memory = MagicMock()
    memory.recall_self_model_async = AsyncMock(return_value=[])
    memory.recall_curiosities_async = AsyncMock(return_value=[])
    memory.recent_feelings_async = AsyncMock(return_value=[])
    memory.recall_async = AsyncMock(return_value=[])
    memory.save_async = AsyncMock()
    memory.format_self_model_for_context = MagicMock(return_value="")
    memory.format_curiosities_for_context = MagicMock(return_value="")
    memory.format_feelings_for_context = MagicMock(return_value="")
    memory.format_for_context = MagicMock(return_value="")
    return memory

@pytest.mark.asyncio
async def test_agent_uses_web_search(mock_config, mock_memory):
    """E2E simulation: Agent decides to search the web."""
    with patch("familiar_agent.agent.ObservationMemory", return_value=mock_memory):
        agent = EmbodiedAgent(mock_config)
        mock_backend = AsyncMock()
        agent.backend = mock_backend
        
        from familiar_agent.backend import TurnResult, ToolCall
        
        # Sequence:
        # 1. LLM decides to search
        # 2. LLM sees results and answers
        mock_backend.stream_turn.side_effect = [
            (
                TurnResult(
                    stop_reason="tool_use", 
                    text="I should look that up.", 
                    tool_calls=[ToolCall(id="c1", name="search", input={"query": "weather in Tokyo"})]
                ),
                []
            ),
            (
                TurnResult(stop_reason="end_turn", text="It is sunny in Tokyo."),
                []
            )
        ]
        
        mock_backend.make_user_message.return_value = {}
        mock_backend.make_assistant_message.return_value = {}
        mock_backend.make_tool_results.return_value = []
        mock_backend.complete.return_value = "neutral"

        # Mock DDG search within the tool
        with patch("familiar_agent.tools.web_tool.DDGS") as mock_ddgs:
            mock_instance = mock_ddgs.return_value.__enter__.return_value
            mock_instance.text.return_value = [{"title": "Weather", "href": "url", "body": "Sunny"}]
            
            await agent.run("How is the weather in Tokyo?")
            
            # Verify that search tool result was passed to backend
            assert mock_backend.make_tool_results.called
            tool_results = mock_backend.make_tool_results.call_args[0][1]
            assert any("Sunny" in str(r) for r in tool_results)
