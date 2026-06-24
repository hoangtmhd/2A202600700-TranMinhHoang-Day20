from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_correctly() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    updated_state = SupervisorAgent().run(state)
    assert len(updated_state.route_history) > 0
    assert updated_state.route_history[-1] == "researcher"
