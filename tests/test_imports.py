def test_core_imports():
    from app.analytics.insights import build_opportunity_insight
    from app.connectors.manager import ConnectorManager
    from app.database.manager import DatabaseManager

    assert ConnectorManager is not None
    assert DatabaseManager is not None
    assert build_opportunity_insight is not None


def test_ceo_workspace_imports():
    from app.services.ceo_workspace_service import CEOWorkspaceService
    from app.database.models import ProductProject, AgentTask, AgentEvent
    assert CEOWorkspaceService is not None
    assert ProductProject is not None
    assert AgentTask is not None
    assert AgentEvent is not None
