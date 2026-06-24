from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        research_notes = state.research_notes or "No research notes available."
        analysis_notes = state.analysis_notes or "No analysis notes available."
        audience = state.request.audience

        sources_text = "\n".join(
            [
                f"- [{i+1}] {src.title} ({src.url or 'No URL'})"
                for i, src in enumerate(state.sources)
            ]
        )

        system_prompt = (
            f"You are a professional writer. Your job is to write a comprehensive, well-structured, "
            f"and polished report answering the user's query.\n"
            f"Target Audience: {audience}\n\n"
            f"Guidelines:\n"
            f"1. Synthesize the findings from the research notes and analysis notes.\n"
            f"2. Present the answer clearly with logical sections.\n"
            f"3. Include citations to the sources (e.g., using [1], [2]) where appropriate.\n"
            f"4. Add a 'References' section at the end listing the source documents."
        )
        user_prompt = (
            f"Research Notes:\n{research_notes}\n\n"
            f"Analysis Notes:\n{analysis_notes}\n\n"
            f"Sources:\n{sources_text}"
        )

        response = self.llm_client.complete(system_prompt, user_prompt)

        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("writer_execution", {})
        return state
