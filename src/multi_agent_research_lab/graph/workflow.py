from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()
        self.graph = self.build()

    def build(self) -> object:
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)

        # Register nodes
        builder.add_node("supervisor", self.supervisor.run)
        builder.add_node("researcher", self.researcher.run)
        builder.add_node("analyst", self.analyst.run)
        builder.add_node("writer", self.writer.run)
        builder.add_node("critic", self.critic.run)

        # Add base transition edges
        builder.add_edge(START, "supervisor")
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "critic")
        builder.add_edge("critic", "supervisor")

        def route_decision(state: ResearchState) -> str:
            if not state.route_history:
                return "done"
            return state.route_history[-1]

        builder.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        result = self.graph.invoke(state)
        
        if isinstance(result, ResearchState):
            return result
        elif isinstance(result, dict):
            return ResearchState(**result)
        return result
