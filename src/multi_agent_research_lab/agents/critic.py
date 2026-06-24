from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        final_answer = state.final_answer or "No final answer available."
        sources_text = "\n".join(
            [
                f"- [{i+1}] {src.title} ({src.url or 'No URL'}): {src.snippet}"
                for i, src in enumerate(state.sources)
            ]
        )

        system_prompt = (
            "You are a strict fact-checker and safety editor. Your job is to review the final answer "
            "against the raw sources provided. Check for:\n"
            "1. Hallucinations or claims not supported by the sources.\n"
            "2. Citation accuracy (do the numbers [1], [2], etc., match the actual references?).\n"
            "3. Safety and neutrality.\n\n"
            "Output your critique, clearly stating if the draft is approved or if it needs revisions."
        )
        user_prompt = (
            f"Final Answer:\n{final_answer}\n\n"
            f"Raw Sources:\n{sources_text}"
        )

        response = self.llm_client.complete(system_prompt, user_prompt)

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("critic_execution", {})
        return state
