from __future__ import annotations

from datetime import datetime

from app.database.models import ProductProject
from app.orchestration.event_bus import EventBus


class WorkflowEngine:
    """Project lifecycle engine for Atlas OS."""

    STAGES = [
        "candidate",
        "approved",
        "research_complete",
        "product_design",
        "manufacturing",
        "finance",
        "marketing",
        "launch",
        "growth",
    ]

    TRANSITIONS = {
        "candidate": ["approved"],
        "approved": ["research_complete"],
        "research_complete": ["product_design", "manufacturing"],
        "product_design": ["manufacturing"],
        "manufacturing": ["finance"],
        "finance": ["marketing"],
        "marketing": ["launch"],
        "launch": ["growth"],
        "growth": [],
    }

    def __init__(self, session):
        self.session = session
        self.event_bus = EventBus(session)

    def can_transition(self, project: ProductProject, next_stage: str) -> bool:
        return next_stage in self.TRANSITIONS.get(project.stage, [])

    def transition(self, project: ProductProject, next_stage: str, agent_name: str = "CEO Agent") -> ProductProject:
        if not self.can_transition(project, next_stage):
            raise ValueError(f"Cannot transition project from {project.stage!r} to {next_stage!r}")

        old_stage = project.stage
        project.stage = next_stage
        project.updated_at = datetime.utcnow()
        self.session.commit()

        self.event_bus.emit(
            project=project,
            agent_name=agent_name,
            event_type="workflow_transition",
            message=f"Project moved from {old_stage} to {next_stage}.",
            payload={"from": old_stage, "to": next_stage},
        )
        return project

    def readiness(self, project: ProductProject) -> int:
        statuses = [
            project.research_status,
            project.product_status,
            project.manufacturing_status,
            project.finance_status,
            project.marketing_status,
            project.customer_success_status,
        ]
        completed = sum(1 for value in statuses if str(value).lower() in {"complete", "completed", "approved"})
        return int((completed / len(statuses)) * 100) if statuses else 0
