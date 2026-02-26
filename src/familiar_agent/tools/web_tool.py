"""Web search and fetching tool - allows the agent to access the internet."""

from __future__ import annotations

import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebTool:
    """Provides search and fetching capabilities."""

    def __init__(self, max_results: int = 5, fetch_limit: int = 2000):
        self.max_results = max_results
        self.fetch_limit = fetch_limit
        logger.info("WebTool initialized. max_results=%d, fetch_limit=%d", max_results, fetch_limit)
    def search(self, query: str) -> str:
        """Search the web using DuckDuckGo."""
        logger.info("Web search starting: query='%s', max_results=%d", query, self.max_results)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))
            
            logger.debug("DDGS returned %d results", len(results))
            
            if not results:
                logger.warning("No search results found for query: %s", query)
                return "No search results found."
            
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(str(i) + ". " + r['title'])
                lines.append("   URL: " + r['href'])
                lines.append("   Summary: " + r['body'])
                lines.append("")
            
            logger.info("Web search completed: %d results returned", len(results))
            return "\n".join(lines)
        except Exception as e:
            logger.error("Search failed for query '%s': %s", query, e)
            return "Error during web search: " + str(e)

    async def fetch(self, url: str, full: bool = False) -> str:
        """Fetch content from a URL."""
        logger.info("Web fetch starting: url='%s' (full=%s)", url, full)
        try:
            import aiohttp
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        logger.warning("Fetch failed: HTTP %d from %s", resp.status, url)
                        return "Error: Received HTTP " + str(resp.status) + " from " + url
                    html = await resp.text()

            logger.debug("Fetched %d bytes from %s", len(html), url)

            # Simple HTML to text conversion
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles, and other noise
            for s in soup(["script", "style", "nav", "footer", "header"]):
                s.decompose()
            
            text = soup.get_text(separator="\n")
            # Clean up whitespace
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            text = "\n".join(lines)

            if not full and len(text) > self.fetch_limit:
                logger.info("Fetch completed: %d chars (truncated from %d)", self.fetch_limit, len(text))
                return text[:self.fetch_limit] + "\n\n--- [Truncated: Page is longer than " + str(self.fetch_limit) + " characters. Use full=True if needed] ---"
            
            logger.info("Fetch completed: %d chars", len(text))
            return text if text else "(No readable text found)"
        except Exception as e:
            logger.error("Fetch failed for URL '%s': %s", url, e)
            return "Error fetching URL: " + str(e)

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "name": "search",
                "description": "Search the web for real-time information, news, or facts.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch",
                "description": "Download and read the text content of a specific webpage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                        "full": {
                            "type": "boolean", 
                            "description": "If True, fetch the entire page. If False, fetch only the beginning (default).",
                            "default": False
                        }
                    },
                    "required": ["url"]
                }
            }
        ]

    async def call(self, tool_name: str, tool_input: dict) -> tuple[str, str | None]:
        if tool_name == "search":
            res = self.search(tool_input["query"])
            return res, None
        elif tool_name == "fetch":
            res = await self.fetch(tool_input["url"], tool_input.get("full", False))
            return res, None
        return "Unknown tool: " + tool_name, None
