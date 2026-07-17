from __future__ import annotations

from app.database.models import AgentEvent, AgentTask, ProductProject
from app.orchestration.workflow_engine import WorkflowEngine


class ProjectWorkspaceService:
    """Read model and actions for one Atlas OS product workspace."""

    def __init__(self, session):
        self.session = session
        self.workflow = WorkflowEngine(session)

    def get_project(self, project_id: int) -> ProductProject:
        project = self.session.query(ProductProject).filter_by(id=project_id).first()
        if project is None:
            raise ValueError(f"ProductProject not found: {project_id}")
        return project

    def workspace(self, project_id: int) -> dict:
        project = self.get_project(project_id)
        tasks = (
            self.session.query(AgentTask)
            .filter_by(project_id=project.id)
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .all()
        )
        events = (
            self.session.query(AgentEvent)
            .filter_by(project_id=project.id)
            .order_by(AgentEvent.created_at.desc())
            .all()
        )
        return {
            "project": project,
            "tasks": tasks,
            "events": events,
            "readiness": self.workflow.readiness(project),
        }
