import os

from app.connectors.sample import SampleConnector
from app.database.manager import DatabaseManager
from app.database.seed import seed_database
from app.agents.research_engine import ResearchEngine
from app.database.models import Opportunity, Keyword
from app.utils.config import load_config
from app.utils.logger import get_logger


def main() -> None:
    logger = get_logger("atlas")
    config = load_config()

    logger.info(
        "Starting %s v%s",
        config["project"]["name"],
        config["project"]["version"],
    )

    db = DatabaseManager()
    db.initialize()

    with db.get_session() as session:
        seed_database(session)

        mode = os.getenv("ATLAS_DATA_MODE", "sample").lower()
        logger.info("Running in %s mode.", mode)

        connector = SampleConnector()
        engine = ResearchEngine(session, connector)
        engine.run_all_enabled(limit=25)

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