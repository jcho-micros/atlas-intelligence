from datetime import datetime
from app.connectors.base import MarketplaceConnector
from app.database.models import Keyword, ResearchRun
from app.services.listing_service import ListingService
from app.services.opportunity_service import OpportunityService
from app.services.snapshot_service import SnapshotService


class ResearchEngine:
    def __init__(self, session, connector: MarketplaceConnector):
        self.session = session
        self.connector = connector
        self.listing_service = ListingService(session)
        self.opportunity_service = OpportunityService(session)
        self.snapshot_service = SnapshotService(session)

    def run_keyword(self, keyword: Keyword, limit: int = 25) -> None:
        run = ResearchRun(keyword_id=keyword.id, connector=self.connector.name, status="started")
        self.session.add(run)
        self.session.commit()
        try:
            keyword.status = "running"
            self.session.commit()
            marketplace_items = self.connector.search(keyword.keyword, limit=limit)
            listings = self.listing_service.save_listings(keyword=keyword, marketplace=self.connector.name, listings=marketplace_items)
            self.opportunity_service.calculate_for_keyword(keyword)
            self.snapshot_service.snapshot_keyword(keyword, run, listings)
            keyword.status = "completed"
            keyword.last_researched_at = datetime.utcnow()
            run.status = "completed"
            run.listings_found = len(listings)
            run.finished_at = datetime.utcnow()
            self.session.commit()
        except Exception as exc:
            keyword.status = "failed"
            run.status = "failed"
            run.error_message = str(exc)
            run.finished_at = datetime.utcnow()
            self.session.commit()
            raise

    def run_all_enabled(self, limit: int = 25) -> None:
        for keyword in self.session.query(Keyword).filter_by(enabled=True).all():
            self.run_keyword(keyword, limit=limit)
