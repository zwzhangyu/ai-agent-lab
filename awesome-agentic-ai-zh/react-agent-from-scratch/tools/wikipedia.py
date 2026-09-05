import wikipediaapi

from tools.base_tool import BaseTool


class WikipediaTool(BaseTool):
    """Fetches structured Wikipedia data for a given topic."""

    def __init__(self):
        super().__init__()
        self.name = "wikipedia"
        self.description = "Searches Wikipedia for general knowledge and factual information."
        self.wiki_api = wikipediaapi.Wikipedia(
            user_agent="ReActAgent/1.0 (react-agent@example.com)",
            language="en",
        )

    def run(self, query: str) -> str:
        if not query or not query.strip():
            return "Error: Query cannot be empty."

        try:
            page = self.wiki_api.page(query)

            if page.exists():
                return {"query": query, "title": page.title, "summary": page.summary}

            return {"error": f"No Wikipedia page found for '{query}'."}

        except Exception as e:
            return {"error": f"An error occurred while searching Wikipedia: {str(e)}"}
