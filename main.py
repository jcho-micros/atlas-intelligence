import os
from app.agents.research_agent import ResearchAgent
from app.database.db import create_session_factory
from app.database.models import Opportunity, Keyword
from app.services.keyword_service import KeywordService
from app.utils.config import load_config, get_db_path
from app.utils.logger import get_logger


def main() -> None:
    logger = get_logger("atlas")
    config = load_config()
    db_path = get_db_path(config)
    Session = create_session_factory(db_path)

    logger.info("Starting %s v%s", config["project"]["name"], config["project"]["version"])
    logger.info("Database: %s", db_path)

    with Session() as session:
        keyword_service = KeywordService(session)
        added = keyword_service.seed_keywords(config.get("seed_keywords", []))
        keywords = keyword_service.list_enabled_keywords()
        logger.info("Seeded %s new keywords. Enabled keywords: %s", added, len(keywords))

        mode = os.getenv("ATLAS_DATA_MODE", "sample").lower()
        agent = ResearchAgent(session, mode=mode)
        agent.run_all(keywords, limit=25)

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
                f"listings {opp.listing_count:<3} | {opp.recommendation:<13} | {opp.notes}"
            )


if __name__ == "__main__":
    main()
