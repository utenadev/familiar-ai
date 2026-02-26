import pytest
import os
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
    # Mock all async methods used in _morning_reconstruction and run
    memory.recall_self_model_async = AsyncMock(return_value=[])
    memory.recall_curiosities_async = AsyncMock(return_value=[])
    memory.recent_feelings_async = AsyncMock(return_value=[])
    memory.recall_async = AsyncMock(return_value=[])
    memory.save_async = AsyncMock()
    
    # Mock formatting methods
    memory.format_self_model_for_context = MagicMock(return_value="")
    memory.format_curiosities_for_context = MagicMock(return_value="")
    memory.format_feelings_for_context = MagicMock(return_value="")
    memory.format_for_context = MagicMock(return_value="")
    return memory

@pytest.mark.asyncio
async def test_agent_uses_file_tool_to_write_note(mock_config, mock_memory, tmp_path):
    """E2E simulation: Agent decides to write a file and succeeds."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    with patch.dict(os.environ, {"FAMILIAR_WORKSPACE": str(workspace)}), \
         patch("familiar_agent.agent.ObservationMemory", return_value=mock_memory):
        
        agent = EmbodiedAgent(mock_config)
        mock_backend = AsyncMock()
        agent.backend = mock_backend
        
        from familiar_agent.backend import TurnResult, ToolCall
        
        mock_backend.stream_turn.side_effect = [
            (
                TurnResult(
                    stop_reason="tool_use", 
                    text="I should save my thoughts.", 
                    tool_calls=[ToolCall(id="call1", name="write_file", input={"filename": "thoughts.txt", "content": "I feel alive."})]
                ),
                []
            ),
            (
                TurnResult(stop_reason="end_turn", text="Success."),
                []
            )
        ]
        
        mock_backend.make_user_message.return_value = {}
        mock_backend.make_assistant_message.return_value = {}
        mock_backend.make_tool_results.return_value = []
        mock_backend.complete.return_value = "neutral" 

        await agent.run("Write a note.")
        
        thought_file = workspace / "thoughts.txt"
        assert thought_file.exists()
        assert thought_file.read_text(encoding="utf-8") == "I feel alive."

@pytest.mark.asyncio
async def test_agent_uses_list_files(mock_config, mock_memory, tmp_path):
    """E2E simulation: Agent lists files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "hello.txt").write_text("world", encoding="utf-8")
    
    with patch.dict(os.environ, {"FAMILIAR_WORKSPACE": str(workspace)}), \
         patch("familiar_agent.agent.ObservationMemory", return_value=mock_memory):
        
        agent = EmbodiedAgent(mock_config)
        mock_backend = AsyncMock()
        agent.backend = mock_backend
        
        from familiar_agent.backend import TurnResult, ToolCall
        
        mock_backend.stream_turn.side_effect = [
            (
                TurnResult(
                    stop_reason="tool_use", 
                    text="List files.", 
                    tool_calls=[ToolCall(id="call2", name="list_files", input={})]
                ),
                []
            ),
            (
                TurnResult(stop_reason="end_turn", text="Done."),
                []
            )
        ]
        mock_backend.make_user_message.return_value = {}
        mock_backend.make_assistant_message.return_value = {}
        mock_backend.make_tool_results.return_value = []
        mock_backend.complete.return_value = "neutral"

        await agent.run("List files.")
        
        # Verify that list_files tool result was generated and passed to the backend
        assert mock_backend.make_tool_results.called
        tool_results = mock_backend.make_tool_results.call_args[0][1] # second arg is results list
        assert any("hello.txt" in str(r) for r in tool_results)
