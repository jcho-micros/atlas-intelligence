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


def test_role_management_is_audited_and_protects_last_owner(tmp_path):
    from app.foundation import RoleAssignmentError

    session, service = make_service(tmp_path)
    result = service.bootstrap()
    org, owner = result["organization"], result["owner"]
    employee = UserIdentity(
        organization_id=org.id,
        email="employee@example.com",
        display_name="Employee User",
    )
    session.add(employee)
    session.commit()

    assert service.assign_role(employee.id, "Employee", actor_id=owner.id)
    assert not service.assign_role(employee.id, "Employee", actor_id=owner.id)
    assert service.roles_for(employee.id) == {"Employee"}
    assert service.can(employee.id, "workflows.execute")
    assert not service.can(employee.id, "access.manage")

    assert service.revoke_role(employee.id, "Employee", actor_id=owner.id)
    assert service.roles_for(employee.id) == set()
    with pytest.raises(RoleAssignmentError):
        service.revoke_role(owner.id, "Owner", actor_id=owner.id)

    assert session.query(AuditEvent).filter_by(action="access.role_assigned").count() == 1
    assert session.query(AuditEvent).filter_by(action="access.role_revoked").count() == 1
    session.close()


def test_only_access_managers_can_change_roles(tmp_path):
    session, service = make_service(tmp_path)
    result = service.bootstrap()
    org = result["organization"]
    viewer_role = session.query(AccessRole).filter_by(organization_id=org.id, name="Viewer").one()
    viewer = UserIdentity(organization_id=org.id, email="viewer2@example.com", display_name="Viewer")
    target = UserIdentity(organization_id=org.id, email="target@example.com", display_name="Target")
    session.add_all([viewer, target])
    session.flush()
    session.add(UserRole(identity_id=viewer.id, role_id=viewer_role.id))
    session.commit()

    with pytest.raises(PermissionDenied):
        service.assign_role(target.id, "Employee", actor_id=viewer.id)
    assert service.roles_for(target.id) == set()
    session.close()
