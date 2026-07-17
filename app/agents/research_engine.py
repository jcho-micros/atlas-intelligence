from datetime import datetime

from app.connectors.base import MarketplaceConnector
from app.database.models import Keyword, ResearchRun
from app.services.candidate_project_service import CandidateProjectService
from app.services.listing_service import ListingService
from app.services.opportunity_service import OpportunityService
from app.services.snapshot_service import SnapshotService
from app.utils.settings import Settings


class ResearchEngine:
    def __init__(self, session, connector: MarketplaceConnector):
        self.session = session
        self.connector = connector
        self.listing_service = ListingService(session)
        self.opportunity_service = OpportunityService(session)
        self.snapshot_service = SnapshotService(session)
        self.candidate_project_service = CandidateProjectService(session)

    def run_keyword(self, keyword: Keyword, limit: int = 25) -> None:
        run = ResearchRun(keyword_id=keyword.id, connector=self.connector.name, status="started")
        self.session.add(run)
        self.session.commit()
        try:
            keyword.status = "running"
            self.session.commit()
            marketplace_items = self.connector.search(keyword.keyword, limit=limit)
            listings = self.listing_service.save_listings(
                keyword=keyword,
                marketplace=self.connector.name,
                listings=marketplace_items,
            )
            opportunity = self.opportunity_service.calculate_for_keyword(keyword)
            self.candidate_project_service.create_from_opportunity(
                keyword=keyword,
                opportunity=opportunity,
                threshold=Settings.CANDIDATE_THRESHOLD,
            )
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
