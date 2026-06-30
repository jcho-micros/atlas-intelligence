from datetime import datetime
from sqlalchemy.orm import Session
from app.connectors.sample import SampleConnector
from app.connectors.etsy import EtsyConnector
from app.database.models import ResearchRun, Keyword
from app.services.listing_service import ListingService
from app.utils.logger import get_logger


class ResearchAgent:
    def __init__(self, session: Session, mode: str = "sample"):
        self.session = session
        self.mode = mode
        self.logger = get_logger("ResearchAgent")
        self.listing_service = ListingService(session)
        self.connector = EtsyConnector() if mode == "etsy" else SampleConnector()

    def research_keyword(self, keyword: Keyword, limit: int = 25) -> ResearchRun:
        self.logger.info("Researching '%s' using %s", keyword.keyword, self.connector.marketplace_name)
        run = ResearchRun(keyword_id=keyword.id, connector=self.connector.marketplace_name, status="running")
        keyword.status = "running"
        self.session.add(run)
        self.session.commit()

        try:
            listings = self.connector.search(keyword.keyword, limit=limit)
            self.listing_service.replace_keyword_listings(keyword, self.connector.marketplace_name, listings)
            run.status = "completed"
            run.listings_found = len(listings)
        except Exception as exc:
            self.logger.exception("Research failed for '%s'", keyword.keyword)
            run.status = "failed"
            run.error_message = str(exc)
            keyword.status = "failed"
        finally:
            run.finished_at = datetime.utcnow()
            self.session.commit()
        return run

    def run_all(self, keywords: list[Keyword], limit: int = 25) -> None:
        for keyword in keywords:
            self.research_keyword(keyword, limit=limit)
