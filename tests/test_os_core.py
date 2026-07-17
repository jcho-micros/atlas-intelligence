from app.agents.core.registry import default_registry
from app.orchestration.workflow_engine import WorkflowEngine


class DummyProject:
    stage = "candidate"


def test_agent_registry_finds_skills():
    registry = default_registry()
    agents = registry.find_by_skill("estimate_costs")
    assert agents
    assert agents[0].name == "Manufacturing Agent"


def test_workflow_allows_expected_transition():
    # Avoids DB access by constructing object without __init__ side effects.
    engine = object.__new__(WorkflowEngine)
    project = DummyProject()
    assert engine.can_transition(project, "approved") is True
    assert engine.can_transition(project, "finance") is False
