from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        research_notes = state.research_notes or "No research notes available."

        system_prompt = (
            "You are a critical research analyst. Your job is to take raw research notes and turn them "
            "into structured insights. Specifically:\n"
            "1. Extract the main claims made in the research.\n"
            "2. Compare different viewpoints or identify any conflicts in the sources.\n"
            "3. Highlight weak evidence, logical gaps, or potential bias.\n"
            "Keep your output objective and analytical."
        )
        user_prompt = f"Research Notes:\n{research_notes}"

        response = self.llm_client.complete(system_prompt, user_prompt)

        state.analysis_notes = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst_execution", {})
        return state
