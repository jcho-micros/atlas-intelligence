from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime

from app.database.models import (
    AgentEvent, CommunicationAction, Conversation, ConversationMessage,
    DesignConcept, DesignEvent, FinanceAnalysis, ProductProject,
    SourcingAssignment, SupplierRecommendation, Vendor, VendorQuote,
)
from app.services.finance_intelligence_service import FinanceIntelligenceService
from app.ai.image_design_provider import ImageDesignProvider


@dataclass
class DesignSummary:
    concepts_created: int
    project_name: str


class DesignManufacturingService:
    """Design-to-sourcing workflow for Atlas v2.7.5.

    A design concept is reviewable for manufacturing only when a real AI image
    has been generated. Provider failures are persisted explicitly instead of
    being hidden behind placeholder artwork.
    """

    IMAGE_ERROR_PREFIX = "atlas-image-error:"

    def __init__(self, session, image_provider=None):
        self.session = session
        self.image_provider = image_provider or ImageDesignProvider()

    def image_provider_status(self):
        return self.image_provider.status()

    @classmethod
    def image_error_message(cls, value: str) -> str | None:
        value = str(value or "")
        if not value.startswith(cls.IMAGE_ERROR_PREFIX):
            return None
        encoded = value[len(cls.IMAGE_ERROR_PREFIX):]
        try:
            return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
        except Exception:
            return "Unknown image generation failure."

    @staticmethod
    def is_ai_image(value: str) -> bool:
        value = str(value or "").strip()
        if not value.startswith("data:image/") or "," not in value:
            return False
        try:
            header, encoded = value.split(",", 1)
            if ";base64" not in header.lower():
                return False
            return bool(base64.b64decode(encoded, validate=True))
        except (ValueError, binascii.Error):
            return False

    @staticmethod
    def image_bytes(value: str) -> bytes:
        """Decode a validated image data URL for Streamlit rendering."""
        if not DesignManufacturingService.is_ai_image(value):
            raise ValueError("The stored design is not a valid AI image data URL.")
        return base64.b64decode(str(value).split(",", 1)[1], validate=True)

    def retry_concept_image(self, concept_id: int) -> DesignConcept:
        concept = self.session.query(DesignConcept).filter_by(id=concept_id).first()
        if concept is None:
            raise ValueError(f"Design concept not found: {concept_id}")
        generated = self._generate_visual(concept.image_prompt)
        concept.mockup_svg = generated
        concept.concept_version = int(concept.concept_version or 1) + 1
        self.session.add(DesignEvent(
            concept_id=concept.id,
            event_type="concept_image_retried",
            actor="Noah Reed",
            message=f"Noah retried AI image generation for {concept.concept_name}.",
        ))
        self.session.commit()
        return concept

    def revise_concept_image(self, concept_id: int, ceo_direction: str) -> DesignConcept:
        """Regenerate one concept using a specific CEO creative direction."""
        concept = self.session.query(DesignConcept).filter_by(id=concept_id).first()
        if concept is None:
            raise ValueError(f"Design concept not found: {concept_id}")
        direction = str(ceo_direction or "").strip()
        if len(direction) < 8:
            raise ValueError("Give Noah a specific design direction before regenerating.")
        project = concept.project
        concept.image_prompt = self._design_prompt(
            project_name=project.project_name,
            concept_name=concept.concept_name,
            rationale=concept.design_rationale,
            materials=concept.materials,
            dimensions=concept.dimensions,
            target=concept.target_customer,
            visual_direction=f"{concept.designer_notes}. CEO REVISION DIRECTION: {direction}",
        )
        concept.mockup_svg = self._generate_visual(concept.image_prompt)
        concept.concept_version = int(concept.concept_version or 1) + 1
        self.session.add(DesignEvent(
            concept_id=concept.id,
            event_type="concept_directed_revision",
            actor="John / CEO",
            message=f"CEO directed revision v{concept.concept_version}: {direction}",
        ))
        self.session.commit()
        return concept

    def regenerate_project_images(self, project_id: int) -> int:
        project = self._project(project_id)
        count = 0
        for concept in project.design_concepts:
            if concept.status == "approved":
                continue
            concept.mockup_svg = self._generate_visual(concept.image_prompt)
            concept.concept_version = int(concept.concept_version or 1) + 1
            self.session.add(DesignEvent(
                concept_id=concept.id,
                event_type="concept_image_regenerated",
                actor="Noah Reed",
                message=f"Noah regenerated the AI image for {concept.concept_name}.",
            ))
            count += 1
        self.session.commit()
        return count

    def generate_concepts(self, project_id: int, refresh: bool = False) -> DesignSummary:
        project = self._project(project_id)
        if refresh:
            for concept in list(project.design_concepts):
                self.session.delete(concept)
            self.session.flush()
        elif project.design_concepts:
            return DesignSummary(len(project.design_concepts), project.project_name)

        idea = project.product_idea
        target = (idea.target_customer if idea else "youth baseball coaches and teams") or "youth baseball coaches and teams"
        base_materials = (idea.materials if idea else "") or "premium acrylic, magnetic components, durable printed graphics"
        price = self._price(project)
        specs = [
            ("Concept A — Field Command", "A clean coach-first system with a full-field layout, strong hierarchy, oversized magnetic player tiles, and a dedicated pitch-count area.", "18 × 24 in", "Dugout-ready, highly legible, minimal visual noise.", "modern professional baseball equipment, navy and warm neutral palette, rugged magnetic dry-erase board"),
            ("Concept B — Heritage Club", "A premium clubhouse aesthetic using warm wood, engraved-style labels, hidden magnetic hardware, and a presentation-forward frame.", "20 × 28 in", "Premium giftable positioning with a traditional baseball feel.", "premium walnut baseball coaching board, engraved details, clubhouse aesthetic, heirloom product"),
            ("Concept C — Travel Pro", "A lightweight folding system optimized for tournament bags, quick setup, weather resistance, and interchangeable roster components.", "14 × 20 in folded", "Compact, durable, and built for coaches moving field to field.", "portable travel baseball coaching system, folding composite shell, weather resistant, tournament dugout"),
        ]
        for idx, (name, rationale, dimensions, notes, visual_direction) in enumerate(specs, 1):
            prompt = self._design_prompt(
                project_name=project.project_name,
                concept_name=name,
                rationale=rationale,
                materials=base_materials,
                dimensions=dimensions,
                target=target,
                visual_direction=visual_direction,
            )
            mockup = self._generate_visual(prompt)
            concept = DesignConcept(
                project_id=project.id, designer_name="Noah Reed", concept_name=name,
                design_rationale=rationale, materials=base_materials, dimensions=dimensions,
                target_customer=target, suggested_price=round(price * (0.94 + idx * 0.04), 2),
                image_prompt=prompt, mockup_svg=mockup,
                designer_notes=notes, status="review",
            )
            self.session.add(concept)
            self.session.flush()
            self.session.add(DesignEvent(concept_id=concept.id, event_type="concept_created", actor="Noah Reed", message=f"Noah created {name} for CEO design review."))
        project.product_status = "design_review"
        project.stage = "design"
        project.readiness_score = max(project.readiness_score or 0, 35)
        self._event(project, "design_concepts_created", "Noah Reed", f"Created three visual design concepts for {project.project_name}.")
        self.session.commit()
        return DesignSummary(3, project.project_name)

    def review_concept(self, concept_id: int, decision: str, note: str = "") -> DesignConcept:
        concept = self.session.query(DesignConcept).filter_by(id=concept_id).first()
        if concept is None:
            raise ValueError(f"Design concept not found: {concept_id}")
        decision = decision.lower().strip()
        if decision not in {"approved", "revision", "rejected"}:
            raise ValueError("Decision must be approved, revision, or rejected")
        if decision == "approved" and not self.is_ai_image(concept.mockup_svg):
            error = self.image_error_message(concept.mockup_svg)
            detail = f" Image provider error: {error}" if error else ""
            raise ValueError(
                "This concept does not have a successful AI-generated product image and cannot "
                f"be approved for Manufacturing.{detail}"
            )
        concept.status = decision
        concept.reviewed_at = datetime.utcnow()
        self.session.add(DesignEvent(concept_id=concept.id, event_type=f"concept_{decision}", actor="John / CEO", message=note or f"CEO marked {concept.concept_name} as {decision}."))
        project = concept.project
        if decision == "approved":
            for other in project.design_concepts:
                if other.id != concept.id and other.status == "approved":
                    other.status = "review"
            project.product_status = "design_approved"
            project.manufacturing_status = "sourcing_assigned"
            project.stage = "manufacturing"
            project.readiness_score = max(project.readiness_score or 0, 45)
            assignment = self.session.query(SourcingAssignment).filter_by(project_id=project.id, design_concept_id=concept.id).first()
            if assignment is None:
                assignment = SourcingAssignment(
                    project_id=project.id, design_concept_id=concept.id, owner_name="David",
                    title=f"Source approved design: {project.project_name}",
                    requirements=f"Build {concept.concept_name}. Materials: {concept.materials}. Dimensions: {concept.dimensions}. {concept.designer_notes}",
                    status="assigned",
                )
                self.session.add(assignment)
            self._event(project, "design_handoff", "Noah Reed", f"Approved {concept.concept_name}; design package handed to David for sourcing.")
        self.session.commit()
        return concept

    def execute_sourcing(self, project_id: int) -> SupplierRecommendation:
        project = self._project(project_id)
        approved = next((c for c in project.design_concepts if c.status == "approved"), None)
        if approved is None:
            raise ValueError("Approve a design concept before manufacturing sourcing.")
        vendors = self.session.query(Vendor).order_by(Vendor.trust_score.desc()).all()
        if not vendors:
            raise ValueError("No vendors are available for sourcing.")
        scored = []
        for vendor in vendors:
            quote = self.session.query(VendorQuote).filter_by(vendor_id=vendor.id).order_by(VendorQuote.landed_cost.asc()).first()
            cost = float(quote.landed_cost or 0) if quote else 0.0
            lead = int(quote.lead_time_days or vendor.average_lead_time_days or 0) if quote else int(vendor.average_lead_time_days or 0)
            moq = int(quote.moq or vendor.minimum_order_quantity or 0) if quote else int(vendor.minimum_order_quantity or 0)
            score = float(vendor.trust_score or 0) + float(vendor.quality_score or 0) * .35 + float(vendor.communication_score or 0) * .2 - min(20, lead * .35) - min(15, moq * .015) - min(20, cost * .25)
            scored.append((score, vendor, quote, cost, lead, moq))
        score, vendor, quote, cost, lead, moq = max(scored, key=lambda x: x[0])
        confidence = max(55.0, min(98.0, round(score, 1)))
        existing = self.session.query(SupplierRecommendation).filter_by(project_id=project.id).first()
        rec = existing or SupplierRecommendation(project_id=project.id, supplier_name=vendor.name)
        rec.vendor_id = vendor.id
        rec.supplier_name = vendor.name
        rec.confidence = confidence
        rec.landed_cost = cost
        rec.lead_time_days = lead
        rec.moq = moq
        rec.status = "recommended"
        rec.reason = f"David recommends {vendor.name}: trust {vendor.trust_score:.0f}, quality {vendor.quality_score:.0f}, communication {vendor.communication_score:.0f}; landed cost ${cost:.2f}, {lead}-day lead time, MOQ {moq}."
        self.session.add(rec)
        for assignment in project.sourcing_assignments:
            assignment.status = "completed"
            assignment.completed_at = datetime.utcnow()
        project.manufacturing_status = "supplier_recommended"
        project.stage = "manufacturing_review"
        project.readiness_score = max(project.readiness_score or 0, 60)
        self._create_handoff_conversation(project, approved, rec)
        self._event(project, "supplier_recommended", "David", rec.reason)
        self.session.commit()
        return rec

    def approve_supplier_and_handoff_finance(self, recommendation_id: int) -> SupplierRecommendation:
        rec = self.session.query(SupplierRecommendation).filter_by(id=recommendation_id).first()
        if rec is None:
            raise ValueError(f"Supplier recommendation not found: {recommendation_id}")
        rec.status = "approved"
        rec.reviewed_at = datetime.utcnow()
        project = rec.project
        project.manufacturing_status = "approved"
        project.finance_status = "pending"
        project.stage = "finance"
        project.readiness_score = max(project.readiness_score or 0, 65)
        self._event(project, "manufacturing_approved", "John / CEO", f"Approved {rec.supplier_name}; Michael received finance handoff.")
        self.session.commit()
        if project.business_id:
            FinanceIntelligenceService(self.session).generate_for_business(project.business_id, refresh=True)
        return rec

    def _create_handoff_conversation(self, project, concept, rec):
        subject = f"Design to manufacturing: {project.project_name}"
        conv = self.session.query(Conversation).filter_by(subject=subject).first()
        if conv is None:
            conv = Conversation(subject=subject, conversation_type="internal", context_type="project", context_name=project.project_name, summary="Noah, David, Mia, and Michael coordinate approved design, sourcing, and finance handoff.", priority=8, status="open")
            self.session.add(conv); self.session.flush()
        self.session.add(ConversationMessage(conversation_id=conv.id, sender_name="Noah Reed", message_type="handoff", body=f"Approved design: {concept.concept_name}. Materials: {concept.materials}. Dimensions: {concept.dimensions}."))
        self.session.add(ConversationMessage(conversation_id=conv.id, sender_name="David", message_type="recommendation", body=rec.reason, requires_response=True))
        self.session.add(CommunicationAction(conversation_id=conv.id, owner_name="Mia Stone", action_type="approval_follow_up", title=f"Track supplier approval for {project.project_name}", status="open"))

    def _project(self, project_id):
        project = self.session.query(ProductProject).filter_by(id=project_id).first()
        if project is None:
            raise ValueError(f"Product project not found: {project_id}")
        return project

    def _price(self, project):
        if project.product:
            lo, hi = float(project.product.suggested_price_min or 0), float(project.product.suggested_price_max or 0)
            if lo or hi: return (lo + hi) / 2 if lo and hi else max(lo, hi)
        if project.product_idea:
            lo, hi = float(project.product_idea.suggested_price_min or 0), float(project.product_idea.suggested_price_max or 0)
            if lo or hi: return (lo + hi) / 2 if lo and hi else max(lo, hi)
        return 59.99

    def _event(self, project, event_type, agent, message):
        self.session.add(AgentEvent(project_id=project.id, agent_name=agent, event_type=event_type, message=message, created_at=datetime.utcnow()))

    def _generate_visual(self, prompt: str) -> str:
        try:
            return self.image_provider.generate(prompt).data_url
        except Exception as exc:
            message = str(exc) or f"{type(exc).__name__}: image generation failed"
            encoded = base64.urlsafe_b64encode(message.encode("utf-8")).decode("ascii")
            return f"{self.IMAGE_ERROR_PREFIX}{encoded}"

    def _design_prompt(self, project_name: str, concept_name: str, rationale: str, materials: str, dimensions: str, target: str, visual_direction: str) -> str:
        concept_key = concept_name.lower()
        if "field command" in concept_key:
            architecture = (
                "A rugged one-piece magnetic coaching command center with a slim powder-coated aluminum frame, "
                "replaceable magnetic player tokens, a clearly separated batting-order rail, a compact field-position zone, "
                "a pitch-count slider, and a fold-flat dugout hook. Strong asymmetric layout; no office-whiteboard appearance."
            )
            styling = "matte navy, charcoal, warm gray, small safety-orange functional accents"
        elif "heritage" in concept_key:
            architecture = (
                "A premium clubhouse object built from a thin walnut veneer frame over an aluminum core, recessed magnetic roster tiles, "
                "a removable tactical field insert, concealed wall/dugout mounting hardware, and refined brass-toned mechanical details. "
                "Modern heritage, not rustic craft signage."
            )
            styling = "walnut, satin black, cream enamel, restrained aged-brass accents"
        else:
            architecture = (
                "A compact folding travel system with two rigid composite panels, a protected center hinge, weather-sealed magnetic pieces, "
                "an integrated carry handle, elastic token storage, and a quick-deploy dugout attachment. It must visibly fold into a coach bag."
            )
            styling = "graphite composite, deep blue, light gray, lime functional accents"

        return f"""
You are Noah Reed, an award-winning industrial designer. Design a genuinely differentiated, patentable-looking physical product—not a decorated rectangle.

PRODUCT: {project_name}
CONCEPT: {concept_name}
BUYER: {target}
USE ENVIRONMENT: youth baseball dugout, dusty fields, wind, hurried lineup changes, gloved or dirty hands
DESIGN INTENT: {rationale}
REQUIRED MATERIALS: {materials}
APPROXIMATE SIZE: {dimensions}
CONSTRUCTION ARCHITECTURE: {architecture}
CMF DIRECTION: {styling}
CREATIVE DIRECTION: {visual_direction}

IMAGE BRIEF:
Create one premium industrial-design hero render of the complete physical product in a realistic three-quarter view. The form, construction, hinge/frame system, thickness, storage, mounting method, magnetic components, and user workflow must be visually obvious. Include only one product, fully inside frame, with a subtle dugout-context backdrop or neutral studio sweep. Use believable injection-molded/composite/aluminum/wood construction, realistic seams, fasteners, radii, shadows, and material transitions. Make it look like a product that could be manufactured and sold for $50–$150.

CRITICAL QUALITY RULES:
- Do not create a generic dry-erase board, poster, infographic, UI screen, flat sign, clipboard, or framed sheet.
- Do not add a large title, marketing headline, logo, brand, watermark, or paragraph of text.
- Avoid generated words and numbers entirely. Use blank magnetic tiles, small color-coded shapes, and icon-like position markers instead of readable text.
- Do not show duplicated positions, nonsensical baseball labels, warped typography, floating parts, or impossible geometry.
- Do not present multiple unrelated concepts, a mood board, exploded diagram, or collage.
- Product silhouette and mechanical innovation matter more than graphics.
- Photorealistic product photography, 50mm lens, controlled softbox lighting, sharp materials, commercially credible proportions.
""".strip()

