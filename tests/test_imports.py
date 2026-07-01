def test_core_imports():
    from app.agents.research_engine import ResearchEngine
    from app.connectors.manager import ConnectorManager
    from app.database.manager import DatabaseManager
    from app.database.models import Keyword, Listing, Opportunity, Project, Shop

    assert ResearchEngine
    assert ConnectorManager
    assert DatabaseManager
    assert Project
    assert Keyword
    assert Listing
    assert Shop
    assert Opportunity
