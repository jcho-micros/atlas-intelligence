from app.agents.research_engine import ResearchEngine
from app.connectors.manager import ConnectorManager
from app.database.manager import DatabaseManager
from app.database.models import Keyword, Opportunity
from app.database.seed import seed_database
from app.utils.config import get_db_path, load_config
from app.utils.logger import get_logger


def main() -> None:
    logger = get_logger("atlas")
    config = load_config()
    db_path = get_db_path(config)
    logger.info("Starting %s v%s", config["project"]["name"], config["project"]["version"])
    logger.info("Database: %s", db_path)
    db = DatabaseManager(db_path)
    db.initialize()

    with db.get_session() as session:
        seed_database(session)
        mode = config["research"]["mode"]
        limit = config["research"]["limit"]
        logger.info("Running in %s mode.", mode)
        connector = ConnectorManager().get_connector(mode)
        logger.info("Using connector: %s", connector.name)
        engine = ResearchEngine(session, connector)
        engine.run_all_enabled(limit=limit)

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
                f"{opp.score:>6} | {kw.keyword[:34]:<34} | avg ${opp.avg_price:<6} | "
                f"listings {opp.listing_count:<3} | {opp.recommendation:<8} | {opp.notes}"
            )


if __name__ == "__main__":
    main()
