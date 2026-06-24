import logging
from tavily import TavilyClient

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client using Tavily with a mock fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.tavily_api_key
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
        else:
            logger.warning("TAVILY_API_KEY is not configured. Falling back to mock search.")
            self.client = None

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if not self.client:
            return self._mock_search(query, max_results)

        try:
            response = self.client.search(query=query, max_results=max_results)
            results = []
            for result in response.get("results", []):
                results.append(
                    SourceDocument(
                        title=result.get("title", "Untitled"),
                        url=result.get("url", ""),
                        snippet=result.get("content", result.get("snippet", "")),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Tavily search API error: {e}. Falling back to mock search.")
            return self._mock_search(query, max_results)

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        """Return dummy search data for testing and offline development."""
        return [
            SourceDocument(
                title=f"Sơ thảo thông tin về: {query}",
                url="https://example.com/mock-search-result",
                snippet=f"Đây là dữ liệu nghiên cứu giả lập cho chủ đề '{query}'. "
                        f"GraphRAG là một phương pháp kết hợp Knowledge Graph và Retrieval-Augmented Generation "
                        f"nhằm cải thiện chất lượng câu trả lời của LLM đối với các truy vấn mang tính tổng hợp toàn cục.",
            )
            for _ in range(max_results)
        ]
