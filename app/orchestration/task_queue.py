from __future__ import annotations

from datetime import datetime

from app.database.models import AgentTask, ProductProject


class TaskQueue:
    """Simple DB-backed task queue for Atlas agents."""

    def __init__(self, session):
        self.session = session

    def create_task(
        self,
        project: ProductProject,
        agent_name: str,
        task_type: str,
        title: str,
        description: str = "",
        priority: int = 5,
        status: str = "pending",
    ) -> AgentTask:
        task = AgentTask(
            project_id=project.id,
            agent_name=agent_name,
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            status=status,
        )
        self.session.add(task)
        self.session.commit()
        return task

    def start_task(self, task_id: int) -> AgentTask:
        task = self._get_task(task_id)
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        self.session.commit()
        return task

    def complete_task(self, task_id: int) -> AgentTask:
        task = self._get_task(task_id)
        task.status = "complete"
        task.completed_at = datetime.utcnow()
        self.session.commit()
        return task

    def pending_for_agent(self, agent_name: str) -> list[AgentTask]:
        return (
            self.session.query(AgentTask)
            .filter_by(agent_name=agent_name, status="pending")
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .all()
        )

    def _get_task(self, task_id: int) -> AgentTask:
        task = self.session.query(AgentTask).filter_by(id=task_id).first()
        if task is None:
            raise ValueError(f"AgentTask not found: {task_id}")
        return task
