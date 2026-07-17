from app.database.manager import DatabaseManager
from app.database.models import Vendor, VendorQuote, VendorEvent
from app.services.vendor_intelligence_service import VendorIntelligenceService


def test_vendor_intelligence_seeds_vendors(tmp_path):
    db = DatabaseManager(str(tmp_path / "atlas.db"))
    db.initialize()
    session = db.get_session()
    try:
        summary = VendorIntelligenceService(session).ensure_seed_vendors()
        assert summary["vendors_total"] >= 4
        assert session.query(Vendor).count() >= 4
        assert session.query(VendorQuote).count() >= 4
        assert session.query(VendorEvent).count() >= 4
    finally:
        session.close()


def test_recommend_vendor_for_lineup_board(tmp_path):
    db = DatabaseManager(str(tmp_path / "atlas.db"))
    db.initialize()
    session = db.get_session()
    try:
        service = VendorIntelligenceService(session)
        service.ensure_seed_vendors()
        vendor = service.recommend_vendor("Premium Magnetic Baseball Lineup Board")
        assert vendor is not None
        assert vendor.category == "Acrylic Fabrication"
        assert vendor.trust_score >= 90
    finally:
        session.close()
