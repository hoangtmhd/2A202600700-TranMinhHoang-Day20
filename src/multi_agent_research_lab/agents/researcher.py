from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self.search_client = SearchClient()
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        query = state.request.query
        max_sources = state.request.max_sources

        # Perform search
        sources = self.search_client.search(query, max_results=max_sources)
        
        # Avoid duplicate sources if researcher is called multiple times
        existing_urls = {src.url for src in state.sources if src.url}
        for src in sources:
            if not src.url or src.url not in existing_urls:
                state.sources.append(src)

        # Synthesize notes using LLM
        sources_text = "\n\n".join(
            [
                f"Source [{i+1}]: {src.title} ({src.url or 'No URL'})\nSnippet: {src.snippet}"
                for i, src in enumerate(sources)
            ]
        )

        system_prompt = (
            "You are a meticulous researcher. Your job is to read search results and synthesize them "
            "into concise, fact-based research notes. Focus on raw data, key facts, and clear references. "
            "Do not analyze implications or write the final report yet. Just extract key findings."
        )
        user_prompt = f"Query: {query}\n\nSearch Results:\n{sources_text}"

        response = self.llm_client.complete(system_prompt, user_prompt)

        state.research_notes = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "sources_count": len(sources),
                },
            )
        )
        state.add_trace_event(
            "researcher_execution", {"query": query, "sources_found": len(sources)}
        )
        return state
