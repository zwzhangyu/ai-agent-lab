import os

from tavily import TavilyClient
from dotenv import load_dotenv

from tools.base_tool import BaseTool


class WebSearchTool(BaseTool):
    """Performs real-time web searches using the Tavily API."""

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Searches the web for up-to-date and real-time information."
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        if self.api_key:
            self.tavily_client = TavilyClient(api_key=self.api_key)
        else:
            self.tavily_client = None

    def run(self, query: str) -> str:
        if not query or not query.strip():
            return [{"error": "Query cannot be empty."}]

        if not self.tavily_client:
            return [{"error": "TAVILY_API_KEY not configured."}]

        try:
            search_results = self.tavily_client.search(query=query, max_results=2)

            if not search_results or "results" not in search_results:
                return [{"error": "No search results available."}]

            formatted_results = []
            for result in search_results["results"]:
                formatted_results.append({
                    "title": result.get("title", "No title available"),
                    "content": result.get("content", "No content available"),
                    "url": result.get("url", "No URL available"),
                    "score": result.get("score", "No score available"),
                })

            return formatted_results if formatted_results else [{"error": "No results found."}]
        except Exception as e:
            return [{"error": f"Search request failed: {str(e)}"}]
