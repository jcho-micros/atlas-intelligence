from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.database.models import AgentEvent, AgentTask, Business, ProductProject


@dataclass
class DepartmentStatus:
    name: str
    status: str
    open_tasks: int
    completed_tasks: int
    current_focus: str
    health_score: int


@dataclass
class BusinessLifecycleState:
    business: Business
    stage: str
    launch_readiness: int
    department_statuses: list[DepartmentStatus]
    risks: list[str]
    next_actions: list[str]
    timeline: list[AgentEvent]


class AutonomousCompanyService:
    """Atlas OS v1.4 service for treating approved businesses as living companies.

    This is intentionally deterministic/local for now. It does not call an LLM.
    It reads existing businesses, product projects, agent tasks, and events, then
    produces executive-level lifecycle, department health, risks, and next actions.
    """

    DEPARTMENTS = [
        "Manufacturing Agent",
        "Finance Agent",
        "Marketing Agent",
        "Customer Success Agent",
        "Logistics Agent",
        "Launch Agent",
    ]

    def __init__(self, session):
        self.session = session

    def portfolio_summary(self) -> dict[str, Any]:
        businesses = self.session.query(Business).all()
        projects = self.session.query(ProductProject).all()
        open_tasks = (
            self.session.query(AgentTask)
            .filter(~AgentTask.status.in_(["complete", "completed", "done"]))
            .all()
        )
        launch_ready = [p for p in projects if (p.readiness_score or 0) >= 75]
        blocked = [p for p in projects if (p.readiness_score or 0) < 45]

        forecast = sum(float(b.estimated_monthly_revenue or 0) for b in businesses)
        margin_values = [float(b.estimated_margin or 0) for b in businesses if b.estimated_margin]
        avg_margin = round(sum(margin_values) / len(margin_values), 1) if margin_values else 0.0
        avg_readiness = round(
            sum(float(p.readiness_score or 0) for p in projects) / len(projects), 1
        ) if projects else 0.0

        return {
            "businesses": len(businesses),
            "projects": len(projects),
            "open_tasks": len(open_tasks),
            "launch_ready": len(launch_ready),
            "blocked": len(blocked),
            "monthly_forecast": round(forecast, 2),
            "annual_forecast": round(forecast * 12, 2),
            "avg_margin": avg_margin,
            "avg_readiness": avg_readiness,
            "brief": self._brief(len(businesses), len(projects), len(open_tasks), len(launch_ready), forecast),
        }

    def lifecycle_for_business(self, business_id: int) -> BusinessLifecycleState:
        business = self.session.query(Business).filter_by(id=business_id).first()
        if business is None:
            raise ValueError(f"Business not found: {business_id}")

        projects = list(business.product_projects)
        readiness = self._launch_readiness(projects)
        stage = self._stage(projects, readiness)
        departments = [self._department_status(business, department) for department in self.DEPARTMENTS]
        risks = self._risks(business, projects, departments)
        next_actions = self._next_actions(stage, departments, risks)
        timeline = self._timeline(business)

        return BusinessLifecycleState(
            business=business,
            stage=stage,
            launch_readiness=readiness,
            department_statuses=departments,
            risks=risks,
            next_actions=next_actions,
            timeline=timeline,
        )

    def bootstrap_business_operating_plan(self, business_id: int) -> BusinessLifecycleState:
        """Create missing operating-system events for an approved business.

        This keeps v1.4 useful even before real external integrations exist. It
        creates one business-level timeline event per department if missing.
        """
        business = self.session.query(Business).filter_by(id=business_id).first()
        if business is None:
            raise ValueError(f"Business not found: {business_id}")

        projects = list(business.product_projects)
        if not projects:
            return self.lifecycle_for_business(business_id)

        anchor_project = projects[0]
        existing_messages = {
            event.message
            for event in self.session.query(AgentEvent)
            .filter(AgentEvent.project_id.in_([p.id for p in projects]))
            .all()
        }
        messages = [
            ("COO Agent", "operating_plan_created", f"COO created operating plan for business: {business.name}"),
            ("Manufacturing Agent", "department_started", "Manufacturing is preparing supplier discovery and cost validation."),
            ("Finance Agent", "department_started", "Finance is preparing unit economics and break-even analysis."),
            ("Marketing Agent", "department_started", "Marketing is preparing SEO, positioning, and launch content."),
            ("Customer Success Agent", "department_started", "Customer Success is preparing FAQs and personalization support flows."),
            ("Launch Agent", "department_waiting", "Launch waits on manufacturing and finance clearance."),
        ]
        for agent_name, event_type, message in messages:
            if message not in existing_messages:
                self.session.add(
                    AgentEvent(
                        project_id=anchor_project.id,
                        agent_name=agent_name,
                        event_type=event_type,
                        message=message,
                        created_at=datetime.utcnow(),
                    )
                )
        self.session.commit()
        return self.lifecycle_for_business(business_id)

    def _brief(self, businesses: int, projects: int, open_tasks: int, launch_ready: int, forecast: float) -> str:
        if businesses == 0:
            return "No active businesses yet. Approve a business opportunity to let Atlas create the first operating company."
        if launch_ready:
            return f"Atlas has {launch_ready} project(s) nearing launch readiness across {businesses} business(es)."
        return f"Atlas is operating {businesses} business(es), {projects} product project(s), and {open_tasks} open department task(s)."

    def _launch_readiness(self, projects: list[ProductProject]) -> int:
        if not projects:
            return 0
        return int(round(sum(p.readiness_score or 0 for p in projects) / len(projects)))

    def _stage(self, projects: list[ProductProject], readiness: int) -> str:
        if not projects:
            return "approved"
        if readiness >= 85:
            return "launch_ready"
        if readiness >= 65:
            return "launching"
        if any((p.manufacturing_status or "") == "pending" for p in projects):
            return "building"
        return "planning"

    def _department_status(self, business: Business, department: str) -> DepartmentStatus:
        project_ids = [p.id for p in business.product_projects]
        if not project_ids:
            return DepartmentStatus(department, "waiting", 0, 0, "No product projects yet", 0)

        tasks = (
            self.session.query(AgentTask)
            .filter(AgentTask.project_id.in_(project_ids), AgentTask.agent_name == department)
            .all()
        )
        completed = [t for t in tasks if t.status in {"complete", "completed", "done"}]
        open_tasks = [t for t in tasks if t.status not in {"complete", "completed", "done"}]

        if not tasks:
            status = "waiting"
            focus = "No assigned work yet"
            health = 40
        elif open_tasks:
            status = "working"
            focus = open_tasks[0].title
            health = max(35, int((len(completed) / max(len(tasks), 1)) * 100))
        else:
            status = "complete"
            focus = "Department work complete"
            health = 100

        return DepartmentStatus(department, status, len(open_tasks), len(completed), focus, health)

    def _risks(self, business: Business, projects: list[ProductProject], departments: list[DepartmentStatus]) -> list[str]:
        risks: list[str] = []
        if not projects:
            risks.append("Business has no product projects yet.")
        if business.estimated_margin and business.estimated_margin < 35:
            risks.append("Estimated margin is below target; Finance should validate pricing and costs.")
        for department in departments:
            if department.name in {"Manufacturing Agent", "Finance Agent"} and department.status != "complete":
                risks.append(f"{department.name.replace(' Agent', '')} is not complete yet.")
        return risks[:5]

    def _next_actions(self, stage: str, departments: list[DepartmentStatus], risks: list[str]) -> list[str]:
        actions: list[str] = []
        for department in departments:
            if department.open_tasks:
                actions.append(f"{department.name}: {department.current_focus}")
        if not actions and stage != "launch_ready":
            actions.append("COO Agent: review readiness and prepare launch checklist.")
        if risks:
            actions.append("CEO: review risks before approving launch.")
        return actions[:6]

    def _timeline(self, business: Business) -> list[AgentEvent]:
        project_ids = [p.id for p in business.product_projects]
        if not project_ids:
            return []
        return (
            self.session.query(AgentEvent)
            .filter(AgentEvent.project_id.in_(project_ids))
            .order_by(AgentEvent.created_at.desc())
            .limit(25)
            .all()
        )
