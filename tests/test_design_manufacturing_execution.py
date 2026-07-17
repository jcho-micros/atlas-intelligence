from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.image_design_provider import GeneratedDesignImage, ImageProviderStatus
from app.database.models import Base, Business, Keyword, Product, ProductProject, Project, Vendor, VendorQuote
from app.services.design_manufacturing_service import DesignManufacturingService


class FakeImageProvider:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def status(self):
        return ImageProviderStatus(
            configured=True,
            provider="Test Provider",
            model="test-image-model",
            size="1536x1024",
            quality="medium",
        )

    def generate(self, prompt: str):
        if self.fail:
            raise RuntimeError("provider quota exceeded")
        return GeneratedDesignImage(
            data_url="data:image/png;base64,dGVzdC1pbWFnZQ==",
            provider="test",
            model="test-image-model",
        )


def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(s):
    research = Project(name="Research")
    s.add(research); s.flush()
    keyword = Keyword(project_id=research.id, keyword="baseball lineup board")
    business = Business(name="Diamond Edge", market="Baseball")
    s.add_all([keyword, business]); s.flush()
    product = Product(business_id=business.id, name="Lineup Board", suggested_price_min=69, suggested_price_max=89)
    s.add(product); s.flush()
    project = ProductProject(keyword_id=keyword.id, business_id=business.id, product_id=product.id, project_name="Premium Magnetic Lineup Board")
    vendor = Vendor(name="CoachWorks Fabrication", trust_score=94, quality_score=96, communication_score=92, average_lead_time_days=9, minimum_order_quantity=50)
    s.add_all([project, vendor]); s.flush()
    s.add(VendorQuote(vendor_id=vendor.id, product_name=project.project_name, unit_cost=18, shipping_cost=3, landed_cost=21, moq=50, lead_time_days=9, quote_status="received"))
    s.commit()
    return project


def test_design_to_finance_workflow():
    s = session(); project = seed(s)
    svc = DesignManufacturingService(s, image_provider=FakeImageProvider())
    summary = svc.generate_concepts(project.id)
    assert summary.concepts_created == 3
    assert len(project.design_concepts) == 3
    assert all(c.mockup_svg.startswith("data:image/") for c in project.design_concepts)
    concept = project.design_concepts[0]
    svc.review_concept(concept.id, "approved", "Use this direction")
    assert project.product_status == "design_approved"
    assert len(project.sourcing_assignments) == 1
    rec = svc.execute_sourcing(project.id)
    assert rec.supplier_name == "CoachWorks Fabrication"
    assert rec.status == "recommended"
    svc.approve_supplier_and_handoff_finance(rec.id)
    assert rec.status == "approved"
    assert project.manufacturing_status == "approved"
    assert s.query(Business).first().finance_analyses


def test_failed_ai_image_is_explicit_and_cannot_be_approved():
    s = session(); project = seed(s)
    svc = DesignManufacturingService(s, image_provider=FakeImageProvider(fail=True))
    svc.generate_concepts(project.id)
    concept = project.design_concepts[0]

    assert svc.image_error_message(concept.mockup_svg) == "provider quota exceeded"

    try:
        svc.review_concept(concept.id, "approved")
        assert False, "approval should fail without a successful AI image"
    except ValueError as exc:
        assert "cannot be approved" in str(exc)
        assert "provider quota exceeded" in str(exc)


def test_retry_increments_concept_version_and_persists_image():
    s = session(); project = seed(s)
    svc = DesignManufacturingService(s, image_provider=FakeImageProvider(fail=True))
    svc.generate_concepts(project.id)
    concept = project.design_concepts[0]
    starting_version = concept.concept_version

    svc.image_provider = FakeImageProvider()
    refreshed = svc.retry_concept_image(concept.id)

    assert refreshed.concept_version == starting_version + 1
    assert svc.is_ai_image(refreshed.mockup_svg)
    assert s.query(type(concept)).filter_by(id=concept.id).one().mockup_svg.startswith("data:image/")


def test_ceo_directed_revision_updates_prompt_image_and_version():
    s = session(); project = seed(s)
    svc = DesignManufacturingService(s, image_provider=FakeImageProvider())
    svc.generate_concepts(project.id)
    concept = project.design_concepts[0]
    starting_version = concept.concept_version

    revised = svc.revise_concept_image(
        concept.id,
        "Make it a fold-flat hard shell with internal magnetic tile storage and no printed words.",
    )

    assert revised.concept_version == starting_version + 1
    assert "CEO REVISION DIRECTION" in revised.image_prompt
    assert "fold-flat hard shell" in revised.image_prompt
    assert svc.is_ai_image(revised.mockup_svg)


def test_ceo_directed_revision_requires_specific_direction():
    s = session(); project = seed(s)
    svc = DesignManufacturingService(s, image_provider=FakeImageProvider())
    svc.generate_concepts(project.id)
    concept = project.design_concepts[0]
    try:
        svc.revise_concept_image(concept.id, "bigger")
        assert False, "short vague directions should fail"
    except ValueError as exc:
        assert "specific design direction" in str(exc)
