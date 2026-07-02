from app.os.enums import AgentName, ProjectStatus, TaskStatus
from app.os.workflow import ProductProject, WorkflowEngine


def test_project_approval_creates_agent_tasks():
    project = ProductProject(
        name="Premium Magnetic Baseball Lineup Board",
        opportunity_keyword="baseball lineup board",
        score=63.54,
    )
    engine = WorkflowEngine()
    engine.approve_project(project)

    assert project.status == ProjectStatus.APPROVED
    assert len(engine.tasks) == 4
    assert engine.tasks[0].agent == AgentName.PRODUCT_DESIGNER
    assert all(task.status == TaskStatus.TODO for task in engine.tasks)
