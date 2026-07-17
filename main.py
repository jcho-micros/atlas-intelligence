from app.agents.research_engine import ResearchEngine
from app.connectors.manager import ConnectorManager
from app.database.manager import DatabaseManager
from app.database.models import Keyword, Opportunity
from app.database.seed import seed_database
from app.employees.employee_service import EmployeeService
from app.employees.workflow_service import EmployeeWorkflowService
from app.foundation import FoundationService
from app.services.vendor_intelligence_service import VendorIntelligenceService
from app.services.finance_intelligence_service import FinanceIntelligenceService
from app.utils.logger import get_logger
from app.utils.settings import Settings


def main() -> None:
    logger = get_logger("atlas")
    logger.info("Starting Atlas Enterprise v2.7.5")
    logger.info("Database: %s", Settings.DB_PATH)
    db = DatabaseManager(Settings.DB_PATH)
    db.initialize()
    with db.get_session() as session:
        seed_database(session)
        FoundationService(session).bootstrap()
        EmployeeService(session).ensure_default_workforce()
        EmployeeWorkflowService(session).ensure_workflows()
        VendorIntelligenceService(session).ensure_seed_vendors()
        FinanceIntelligenceService(session).ensure_finance_for_all_businesses()
        logger.info("Running in %s mode.", Settings.MODE)
        connector = ConnectorManager().get_connector(Settings.MODE)
        logger.info("Using connector: %s", connector.name)
        engine = ResearchEngine(session, connector)
        engine.run_all_enabled(limit=Settings.SEARCH_LIMIT)
        opportunities = (
            session.query(Opportunity, Keyword)
            .join(Keyword, Opportunity.keyword_id == Keyword.id)
            .order_by(Opportunity.score.desc())
            .all()
        )
        print("\nTop Opportunities")
        print("-" * 90)
        for opp, kw in opportunities[:10]:
            print(
                f"{opp.score:>6} | {kw.keyword[:34]:<34} | "
                f"avg ${opp.avg_price:<6} | listings {opp.listing_count:<3} | "
                f"{opp.recommendation:<8} | {opp.notes}"
            )


if __name__ == "__main__":
    main()
