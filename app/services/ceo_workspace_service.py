from __future__ import annotations

from datetime import datetime

from app.database.models import AgentEvent, AgentTask, CandidateProject, Keyword, ProductProject
from app.services.launch_plan_service import LaunchPlanService
from app.services.product_idea_service import ProductIdeaService
from app.services.business_service import BusinessService


class CEOWorkspaceService:
    """CEO Inbox and project lifecycle service for Atlas OS."""

    def __init__(self, session):
        self.session = session
        self.product_idea_service = ProductIdeaService(session)
        self.launch_plan_service = LaunchPlanService(session)
        self.business_service = BusinessService(session)

    def candidate_projects(self, status: str = "candidate") -> list[CandidateProject]:
        return (
            self.session.query(CandidateProject)
            .filter_by(status=status)
            .order_by(CandidateProject.priority.desc(), CandidateProject.confidence.desc(), CandidateProject.created_at.desc())
            .all()
        )

    def park_candidate(self, candidate_id: int) -> CandidateProject:
        candidate = self._candidate(candidate_id)
        candidate.status = "parked"
        candidate.reviewed_at = datetime.utcnow()
        self.session.commit()
        return candidate

    def reject_candidate(self, candidate_id: int) -> CandidateProject:
        candidate = self._candidate(candidate_id)
        candidate.status = "rejected"
        candidate.reviewed_at = datetime.utcnow()
        self.session.commit()
        return candidate

    def approve_candidate(self, candidate_id: int) -> ProductProject:
        candidate = self._candidate(candidate_id)
        if candidate.keyword_id is None:
            raise ValueError("Candidate has no keyword_id and cannot become a product project.")

        keyword = self.session.query(Keyword).filter_by(id=candidate.keyword_id).first()
        if keyword is None:
            raise ValueError(f"Unknown keyword id: {candidate.keyword_id}")

        existing = (
            self.session.query(ProductProject)
            .filter_by(keyword_id=keyword.id, project_name=candidate.title)
            .order_by(ProductProject.created_at.desc())
            .first()
        )
        if existing:
            candidate.status = "approved"
            candidate.reviewed_at = datetime.utcnow()
            self.session.commit()
            return existing

        product_idea = self.product_idea_service.latest_for_keyword(keyword.keyword)
        if product_idea is None:
            self.product_idea_service.generate_for_keyword(keyword.keyword)
            product_idea = self.product_idea_service.latest_for_keyword(keyword.keyword)

        launch_plan = self.launch_plan_service.latest_for_keyword(keyword.keyword)
        if launch_plan is None:
            launch_plan = self.launch_plan_service.generate_for_keyword(keyword.keyword)

        readiness = self._readiness_score(keyword, product_idea, launch_plan)
        project = ProductProject(
            keyword_id=keyword.id,
            product_idea_id=product_idea.id if product_idea else None,
            project_name=candidate.title,
            status="active",
            stage="agent_review",
            readiness_score=readiness,
            priority=candidate.priority,
            research_status="complete",
            product_status="complete" if product_idea else "pending",
            manufacturing_status="pending",
            finance_status="pending",
            marketing_status="pending",
            customer_success_status="pending",
            launch_status="not_started",
            summary=candidate.summary or self._project_summary(keyword, product_idea, readiness),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(project)
        self.session.flush()

        candidate.status = "approved"
        candidate.reviewed_at = datetime.utcnow()

        self._create_default_tasks(project)
        self._event(project, "CEO Agent", "candidate_approved", f"CEO approved candidate project: {candidate.title}")
        self._event(project, "Research Agent", "research_complete", f"Research complete for opportunity: {keyword.keyword}")
        self._event(project, "Product Designer Agent", "product_ready", f"Product concept ready: {project.project_name}")
        self._event(project, "Operations Agent", "agent_pipeline_started", "Manufacturing, finance, marketing, and customer success tasks were created.")

        business = self.business_service.create_or_attach_business_for_project(candidate, project)
        self.business_service.create_opportunity_from_candidate(candidate)
        self._event(project, "COO Agent", "business_workspace_ready", f"Business workspace ready: {business.name}")

        self.session.commit()
        return project

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
        # Kept for compatibility with older dashboard flows.
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            raise ValueError(f"Unknown keyword: {keyword_text}")
        candidate = CandidateProject(
            keyword_id=keyword.id,
            opportunity_id=keyword.opportunity.id if keyword.opportunity else None,
            title=f"Premium {keyword.keyword.title()}",
            summary=keyword.opportunity.notes if keyword.opportunity else "Manual project created from opportunity.",
            confidence=keyword.opportunity.score if keyword.opportunity else 50,
            estimated_margin=0,
            priority=6,
            reason="manual CEO project creation",
            status="candidate",
        )
        self.session.add(candidate)
        self.session.commit()
        return self.approve_candidate(candidate.id)

    def daily_brief(self) -> dict:
        projects = self.session.query(ProductProject).all()
        tasks = self.session.query(AgentTask).all()
        candidates = self.session.query(CandidateProject).filter_by(status="candidate").all()
        open_tasks = [t for t in tasks if t.status not in {"complete", "completed"}]
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
            "candidates": len(candidates),
            "open_tasks": len(open_tasks),
            "launch_ready": len(launch_ready),
            "needs_attention": len(needs_attention),
            "recent_events": recent_events,
            "headline": self._headline(projects, candidates, open_tasks, launch_ready, needs_attention),
        }

    def _candidate(self, candidate_id: int) -> CandidateProject:
        candidate = self.session.query(CandidateProject).filter_by(id=candidate_id).first()
        if candidate is None:
            raise ValueError(f"CandidateProject not found: {candidate_id}")
        return candidate

    def _headline(self, projects, candidates, open_tasks, launch_ready, needs_attention) -> str:
        if candidates:
            return f"Atlas found {len(candidates)} candidate project(s) waiting for CEO review."
        if launch_ready:
            return f"{len(launch_ready)} project(s) are nearing launch readiness."
        if needs_attention:
            return f"{len(needs_attention)} project(s) need agent review before launch."
        if projects:
            return f"{len(projects)} active project(s) with {len(open_tasks)} open agent task(s)."
        return "No active product projects yet. Run research to let Atlas create candidates."

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
            ("CEO Agent", "ceo_review", "Review and approve product project", "complete", "Candidate approved and assigned to agents."),
            ("Research Agent", "research_validation", "Validate opportunity signals and competitor context", "complete", "Market research and scoring are available."),
            ("Product Designer Agent", "product_design", "Generate product concept and listing draft", "complete", "Product idea, title, tags, FAQ, and image prompt are available."),
            ("Manufacturing Agent", "supplier_discovery", "Find at least three vendor paths and request sample cost", "pending", "Need real supplier quotes before launch."),
            ("Logistics Agent", "shipping_estimate", "Estimate packaging, shipping methods, and damage risk", "pending", "Need package dimensions and carrier estimates."),
            ("Finance Agent", "unit_economics", "Calculate unit economics with real vendor cost", "pending", "Need real COGS, shipping, ads, and marketplace fee model."),
            ("Marketing Agent", "launch_assets", "Prepare SEO, Pinterest, social, and launch copy", "pending", "Listing draft exists; launch assets need review."),
            ("Customer Success Agent", "support_docs", "Prepare personalization, FAQ, refund, and support templates", "pending", "FAQ draft exists; policy review needed."),
            ("Launch Agent", "launch_checklist", "Create launch checklist and publication decision", "not_started", "Launch waits on manufacturing and finance approval."),
        ]
        for agent_name, task_type, title, status, description in tasks:
            self.session.add(
                AgentTask(
                    project_id=project.id,
                    agent_name=agent_name,
                    task_type=task_type,
                    title=title,
                    description=description,
                    status=status,
                    priority=9 if status == "pending" else 6,
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
