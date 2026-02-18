"""Web search tool using DuckDuckGo."""

import asyncio
from typing import Dict, Any, List
from duckduckgo_search import DDGS
from app.tools.base import BaseTool, ToolOutput


class WebSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo."""
    
    name = "web_search"
    description = (
        "Search the web for information. "
        "Input should be a search query string. "
        "Returns a list of search results with titles, snippets, and URLs."
    )
    
    def __init__(self, max_results: int = 5):
        """
        Initialize the web search tool.
        
        Args:
            max_results: Maximum number of search results to return
        """
        super().__init__()
        self.max_results = max_results
    
    async def execute(self, query: str, **kwargs) -> ToolOutput:
        """
        Execute a web search.
        
        Args:
            query: The search query string
            **kwargs: Additional arguments (ignored)
            
        Returns:
            ToolOutput: Search results or error
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                query
            )
            
            if not results:
                return ToolOutput(
                    success=True,
                    result="No results found for the query.",
                    error=None
                )
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results[:self.max_results], 1):
                formatted_results.append({
                    "position": idx,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", "")
                })
            
            # Create summary text
            summary = f"Found {len(formatted_results)} results:\n\n"
            for res in formatted_results:
                summary += f"{res['position']}. {res['title']}\n"
                summary += f"   {res['snippet']}\n"
                summary += f"   URL: {res['url']}\n\n"
            
            return ToolOutput(
                success=True,
                result=summary,
                error=None
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Web search failed: {str(e)}"
            )
    
    def _search_sync(self, query: str) -> List[Dict[str, Any]]:
        """
        Synchronous search method.
        
        Args:
            query: The search query
            
        Returns:
            List of search results
        """
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=self.max_results))
            return results
