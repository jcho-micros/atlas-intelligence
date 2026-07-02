from __future__ import annotations

from datetime import datetime

from app.database.models import AgentEvent, AgentTask, Keyword, ProductProject
from app.services.launch_plan_service import LaunchPlanService
from app.services.product_idea_service import ProductIdeaService


class CEOWorkspaceService:
    """Creates and manages product projects for Atlas OS."""

    def __init__(self, session):
        self.session = session
        self.product_idea_service = ProductIdeaService(session)
        self.launch_plan_service = LaunchPlanService(session)

    def latest_project_for_keyword(self, keyword_text: str) -> ProductProject | None:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            return None
        return (
            self.session.query(ProductProject)
            .filter_by(keyword_id=keyword.id)
            .order_by(ProductProject.created_at.desc())
            .first()
        )

    def create_project_from_keyword(self, keyword_text: str) -> ProductProject:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            raise ValueError(f"Unknown keyword: {keyword_text}")

        product_idea = self.product_idea_service.latest_for_keyword(keyword_text)
        if product_idea is None:
            product_idea = self.product_idea_service.generate_for_keyword(keyword_text)

        launch_plan = self.launch_plan_service.latest_for_keyword(keyword_text)
        if launch_plan is None:
            launch_plan = self.launch_plan_service.generate_for_keyword(keyword_text)

        readiness = self._readiness_score(keyword, product_idea, launch_plan)
        project = ProductProject(
            keyword_id=keyword.id,
            product_idea_id=product_idea.id if product_idea else None,
            project_name=product_idea.product_name if product_idea else keyword.keyword.title(),
            status="active",
            stage="operations_review",
            readiness_score=readiness,
            priority=8 if readiness >= 70 else 6,
            research_status="complete",
            product_status="complete" if product_idea else "pending",
            manufacturing_status="review_needed",
            finance_status="review_needed",
            marketing_status="draft_ready",
            customer_success_status="draft_ready",
            launch_status="not_started",
            summary=self._project_summary(keyword, product_idea, readiness),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(project)
        self.session.flush()

        self._create_default_tasks(project)
        self._event(project, "ceo", "project_created", f"CEO Agent created project: {project.project_name}")
        self._event(project, "research", "complete", f"Research complete for opportunity: {keyword.keyword}")
        self._event(project, "product_designer", "complete", f"Product concept generated: {project.project_name}")
        self._event(project, "operations", "pending", "Operations agents are ready for manufacturing, finance, logistics, and launch review.")

        self.session.commit()
        return project

    def daily_brief(self) -> dict:
        projects = self.session.query(ProductProject).all()
        tasks = self.session.query(AgentTask).all()
        open_tasks = [t for t in tasks if t.status != "complete"]
        launch_ready = [p for p in projects if p.readiness_score >= 75]
        needs_attention = [p for p in projects if p.readiness_score < 55]
        recent_events = (
            self.session.query(AgentEvent)
            .order_by(AgentEvent.created_at.desc())
            .limit(8)
            .all()
        )
        return {
            "projects": len(projects),
            "open_tasks": len(open_tasks),
            "launch_ready": len(launch_ready),
            "needs_attention": len(needs_attention),
            "recent_events": recent_events,
            "headline": self._headline(projects, open_tasks, launch_ready, needs_attention),
        }

    def _headline(self, projects, open_tasks, launch_ready, needs_attention) -> str:
        if not projects:
            return "No active product projects yet. Create one from a researched opportunity."
        if launch_ready:
            return f"{len(launch_ready)} project(s) are nearing launch readiness."
        if needs_attention:
            return f"{len(needs_attention)} project(s) need agent review before launch."
        return f"{len(projects)} active project(s) with {len(open_tasks)} open agent task(s)."

    def _readiness_score(self, keyword: Keyword, product_idea, launch_plan) -> int:
        score = 20
        if keyword.opportunity:
            score += min(25, int(keyword.opportunity.score * 0.35))
        if product_idea:
            score += 20
            score += min(15, int(product_idea.confidence * 0.15))
        if launch_plan:
            score += 15
        return max(0, min(100, score))

    def _project_summary(self, keyword: Keyword, product_idea, readiness: int) -> str:
        if product_idea:
            return (
                f"{product_idea.product_name} was created from the '{keyword.keyword}' opportunity. "
                f"Atlas recommends agent review before launch. Current readiness score: {readiness}."
            )
        return f"Product project created from '{keyword.keyword}'. Current readiness score: {readiness}."

    def _create_default_tasks(self, project: ProductProject) -> None:
        tasks = [
            ("CEO Agent", "Review opportunity and approve product project", "complete", "Product project created and assigned to agents."),
            ("Research Agent", "Validate opportunity signals and competitor context", "complete", "Market research and scoring are available."),
            ("Product Designer Agent", "Generate product concept and listing draft", "complete", "Product idea, title, tags, FAQ, and image prompt are available."),
            ("Manufacturing Agent", "Find at least three vendor paths and request sample cost", "pending", "Need real supplier quotes before launch."),
            ("Logistics Agent", "Estimate packaging, shipping methods, and damage risk", "pending", "Need package dimensions and carrier estimates."),
            ("Finance Agent", "Calculate unit economics with real vendor cost", "pending", "Need real COGS, shipping, ads, and marketplace fee model."),
            ("Marketing Agent", "Prepare SEO, Pinterest, social, and launch copy", "draft", "Listing draft exists; launch assets need review."),
            ("Customer Success Agent", "Prepare personalization, FAQ, refund, and support templates", "draft", "FAQ draft exists; policy review needed."),
            ("Launch Agent", "Create launch checklist and publication decision", "not_started", "Launch waits on manufacturing and finance approval."),
        ]
        for agent_name, task_name, status, output in tasks:
            self.session.add(
                AgentTask(
                    project_id=project.id,
                    agent_name=agent_name,
                    task_name=task_name,
                    status=status,
                    priority=9 if status == "pending" else 6,
                    output=output,
                    completed_at=datetime.utcnow() if status == "complete" else None,
                )
            )

    def _event(self, project: ProductProject, agent_name: str, event_type: str, message: str) -> None:
        self.session.add(
            AgentEvent(
                project_id=project.id,
                agent_name=agent_name,
                event_type=event_type,
                message=message,
                created_at=datetime.utcnow(),
            )
        )
