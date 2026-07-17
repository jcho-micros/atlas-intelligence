import pytest

from app.database.manager import DatabaseManager
from app.database.models import AccessRole, AuditEvent, Notification, UserIdentity, UserRole
from app.foundation import FoundationService, PermissionDenied


def make_service(tmp_path):
    db = DatabaseManager(str(tmp_path / "foundation.db"))
    db.initialize()
    session = db.get_session()
    return session, FoundationService(session)


def test_bootstrap_is_idempotent_and_owner_has_all_permissions(tmp_path):
    session, service = make_service(tmp_path)
    first = service.bootstrap()
    second = service.bootstrap()

    assert first["organization"].id == second["organization"].id
    assert session.query(UserIdentity).count() == 1
    assert session.query(AccessRole).count() == 5
    assert service.can(first["owner"].id, "access.manage")
    assert service.can(first["owner"].id, "finance.manage")
    assert session.query(AuditEvent).filter_by(action="foundation.bootstrap").count() == 2
    session.close()


def test_role_permissions_enforce_access(tmp_path):
    session, service = make_service(tmp_path)
    result = service.bootstrap()
    org = result["organization"]
    viewer_role = session.query(AccessRole).filter_by(organization_id=org.id, name="Viewer").one()
    viewer = UserIdentity(
        organization_id=org.id,
        email="viewer@example.com",
        display_name="Read Only User",
    )
    session.add(viewer)
    session.flush()
    session.add(UserRole(identity_id=viewer.id, role_id=viewer_role.id))
    session.commit()

    assert service.can(viewer.id, "company.read")
    assert not service.can(viewer.id, "company.manage")
    with pytest.raises(PermissionDenied):
        service.require(viewer.id, "company.manage")

    denied = session.query(AuditEvent).filter_by(action="access.denied", outcome="denied").one()
    assert denied.actor_name == "Read Only User"
    session.close()


def test_notification_lifecycle_is_audited(tmp_path):
    session, service = make_service(tmp_path)
    result = service.bootstrap()
    org, owner = result["organization"], result["owner"]
    notification = service.notify(
        org.id,
        "Approval needed",
        "Review the manufacturing budget.",
        recipient_id=owner.id,
        severity="warning",
        notification_type="approval",
        resource_type="budget",
        resource_id="42",
    )
    session.commit()

    assert session.query(Notification).filter_by(status="unread").count() == 1
    assert service.mark_notification_read(notification.id, owner.id)
    session.refresh(notification)
    assert notification.status == "read"
    assert notification.read_at is not None
    assert session.query(AuditEvent).filter_by(action="notification.read").count() == 1
    session.close()
