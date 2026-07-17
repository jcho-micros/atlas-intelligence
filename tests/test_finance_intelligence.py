from app.database.manager import DatabaseManager
from app.database.models import Business, FinanceAnalysis, FinanceScenario, Keyword, ProductProject, Project
from app.services.finance_intelligence_service import FinanceIntelligenceService


def test_finance_analysis_creates_unit_economics(tmp_path):
    db = DatabaseManager(str(tmp_path / "atlas.db"))
    db.initialize()
    session = db.get_session()
    try:
        project = Project(name="Test", description="Test")
        session.add(project)
        session.flush()
        keyword = Keyword(project_id=project.id, keyword="test product", category="Test")
        business = Business(name="Test Business", brand_name="Test Brand", market="Test", confidence=80)
        session.add_all([keyword, business])
        session.flush()
        product_project = ProductProject(
            keyword_id=keyword.id,
            business_id=business.id,
            project_name="Premium Test Product",
            status="active",
            stage="manufacturing",
            readiness_score=40,
        )
        session.add(product_project)
        session.commit()

        summary = FinanceIntelligenceService(session).generate_for_business(business.id)

        assert summary.analyses_created == 1
        assert summary.average_margin > 0
        assert summary.monthly_profit_estimate >= 0
        assert session.query(FinanceAnalysis).count() == 1
        assert session.query(FinanceScenario).count() == 3
        assert product_project.finance_status in {"approved", "review", "rejected"}
    finally:
        session.close()
