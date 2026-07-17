from app.database.manager import DatabaseManager
from app.database.models import CommunicationAction, Conversation, ConversationMessage
from app.employees.employee_service import EmployeeService
from app.services.communications_service import CommunicationsService
from app.services.vendor_intelligence_service import VendorIntelligenceService


def test_communications_seed(tmp_path):
    db = DatabaseManager(str(tmp_path / "atlas.db"))
    db.initialize()
    with db.get_session() as session:
        EmployeeService(session).ensure_default_workforce()
        VendorIntelligenceService(session).ensure_seed_vendors()
        summary = CommunicationsService(session).ensure_seed_conversations()

        assert summary["open_conversations"] >= 3
        assert session.query(Conversation).count() >= 3
        assert session.query(ConversationMessage).count() >= 3
        assert session.query(CommunicationAction).count() >= 3
