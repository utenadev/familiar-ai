import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from familiar_agent.tools.web_tool import WebTool

@pytest.fixture
def web_tool():
    return WebTool()

def test_search_mock(web_tool):
    """Test web search with mocked DuckDuckGo."""
    with patch("familiar_agent.tools.web_tool.DDGS") as mock_ddgs:
        # Mocking the context manager and the text method
        mock_instance = mock_ddgs.return_value.__enter__.return_value
        mock_instance.text.return_value = [
            {"title": "Python", "href": "https://python.org", "body": "Best language."}
        ]
        
        result = web_tool.search("Python language")
        assert "Python" in result
        assert "https://python.org" in result
        assert "Best language." in result

@pytest.mark.asyncio
async def test_fetch_mock(web_tool):
    """Test web fetch with mocked aiohttp."""
    mock_html = "<html><body><script>alert(1)</script><nav>Link</nav><h1>Target Content</h1></body></html>"
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock the async context manager and the response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text.return_value = mock_html
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        result = await web_tool.fetch("https://example.com")
        
        # Verify noise reduction (scripts and nav should be removed)
        assert "alert(1)" not in result
        assert "Link" not in result
        assert "Target Content" in result

@pytest.mark.asyncio
async def test_fetch_truncation(web_tool):
    """Test that fetched content is truncated."""
    mock_html = "A" * 5000
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text.return_value = mock_html
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        # Default limit is 2000
        result = await web_tool.fetch("https://example.com", full=False)
        assert "--- [Truncated" in result
        assert len(result) < 3000
        
        # Full content
        full_result = await web_tool.fetch("https://example.com", full=True)
        assert "--- [Truncated" not in full_result
        assert len(full_result) >= 5000
