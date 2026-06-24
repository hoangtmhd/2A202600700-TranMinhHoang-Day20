import json
import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        # Guardrail: Enforce max iterations
        if state.iteration >= self.settings.max_iterations:
            next_step = "done" if state.final_answer else "writer"
            state.record_route(next_step)
            state.add_trace_event(
                "supervisor_max_iterations_reached",
                {"iteration": state.iteration, "next_step": next_step},
            )
            return state

        # Prompt LLM to decide on routing dynamically
        system_prompt = (
            "You are a master research supervisor. Your job is to orchestrate a research team consisting of:\n"
            "- 'researcher': finds facts and collects source documents.\n"
            "- 'analyst': compares viewpoints, extracts claims, and analyzes evidence.\n"
            "- 'writer': synthesizes the notes and writes the final report.\n\n"
            "Analyze the current state of the research project and decide who should run next.\n"
            "Return a JSON object with keys:\n"
            "- 'next': one of ['researcher', 'analyst', 'writer', 'done'].\n"
            "- 'reason': a brief explanation of your decision.\n\n"
            "Rules:\n"
            "1. If no research has been done yet (research_notes is empty/missing), call 'researcher'.\n"
            "2. If research is done but no analysis is written (analysis_notes is empty/missing), call 'analyst'.\n"
            "3. If both research and analysis are done but no final answer is written, call 'writer'.\n"
            "4. If you have a solid research, analysis, and final report, choose 'done' to terminate the workflow.\n"
            "5. If the draft needs revision or more sources, you may route back to 'researcher' or 'analyst'.\n\n"
            "Ensure you return ONLY a raw JSON string like: {\"next\": \"researcher\", \"reason\": \"no notes yet\"}"
        )

        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Current Iteration: {state.iteration}\n"
            f"Has Sources: {len(state.sources) > 0}\n"
            f"Research Notes: {'Present' if state.research_notes else 'Empty'}\n"
            f"Analysis Notes: {'Present' if state.analysis_notes else 'Empty'}\n"
            f"Final Answer: {'Present' if state.final_answer else 'Empty'}\n"
            f"Route History: {state.route_history}"
        )

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            content = response.content.strip()
            
            # Clean potential Markdown formatting from LLM output
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()

            data = json.loads(content)
            next_step = data.get("next", "done")
            reason = data.get("reason", "unknown")

            if next_step not in ["researcher", "analyst", "writer", "done"]:
                next_step = "done"

        except Exception as e:
            # Safe fallback logic
            next_step = "writer" if (state.research_notes and state.analysis_notes) else "researcher"
            reason = f"Error parsing supervisor decision: {e}. Fallback to {next_step}"
            logger.error(reason)

        state.record_route(next_step)
        state.add_trace_event(
            "supervisor_routing_decision",
            {"next_step": next_step, "reason": reason, "iteration": state.iteration},
        )
        return state
