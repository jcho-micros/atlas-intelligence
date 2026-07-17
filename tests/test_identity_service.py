import pytest

from app.core.identity import (
    Department,
    DuplicateIdentity,
    IdentityDisabled,
    IdentityService,
    IdentityStatus,
    IdentityType,
    InvalidManager,
)
from app.database.manager import DatabaseManager
from app.database.models import Organization


def make_service(tmp_path):
    db = DatabaseManager(str(tmp_path / "identity.db"))
    db.initialize()
    session = db.get_session()
    organization = Organization(name="Test Company", slug="test-company")
    session.add(organization)
    session.commit()
    return session, organization, IdentityService(session)


def test_create_human_and_ai_identities(tmp_path):
    session, organization, service = make_service(tmp_path)

    owner = service.create_identity(
        organization_id=organization.id,
        display_name="John Cho",
        identity_type=IdentityType.HUMAN,
        email=" JOHN@EXAMPLE.COM ",
        department=Department.EXECUTIVE,
    )
    researcher = service.create_identity(
        organization_id=organization.id,
        display_name="Atlas Researcher",
        identity_type=IdentityType.AI_EMPLOYEE,
        system_name="Atlas Researcher",
        department=Department.RESEARCH,
        manager_id=owner.id,
    )

    assert owner.email == "john@example.com"
    assert researcher.system_name == "atlas-researcher"
    assert researcher.manager_id == owner.id
    assert service.get_identity(researcher.id) == researcher
    session.close()


def test_duplicate_identifiers_are_rejected_per_organization(tmp_path):
    session, organization, service = make_service(tmp_path)
    service.create_identity(
        organization_id=organization.id,
        display_name="First User",
        identity_type=IdentityType.HUMAN,
        email="person@example.com",
    )

    with pytest.raises(DuplicateIdentity):
        service.create_identity(
            organization_id=organization.id,
            display_name="Duplicate User",
            identity_type=IdentityType.HUMAN,
            email="PERSON@example.com",
        )
    session.close()


def test_status_lifecycle_blocks_disabled_identity(tmp_path):
    session, organization, service = make_service(tmp_path)
    identity = service.create_identity(
        organization_id=organization.id,
        display_name="Automation",
        identity_type=IdentityType.SERVICE_ACCOUNT,
        system_name="workflow-runner",
    )

    suspended = service.suspend_identity(identity.id)
    assert suspended.status is IdentityStatus.SUSPENDED
    with pytest.raises(IdentityDisabled):
        service.require_active(identity.id)

    disabled = service.disable_identity(identity.id)
    assert disabled.status is IdentityStatus.DISABLED

    active = service.activate_identity(identity.id)
    assert service.require_active(active.id).status is IdentityStatus.ACTIVE
    session.close()


def test_manager_must_be_active_and_in_same_organization(tmp_path):
    session, organization, service = make_service(tmp_path)
    worker = service.create_identity(
        organization_id=organization.id,
        display_name="Worker",
        identity_type=IdentityType.AI_EMPLOYEE,
        system_name="worker",
    )

    with pytest.raises(InvalidManager):
        service.assign_manager(worker.id, worker.id)
    with pytest.raises(InvalidManager):
        service.assign_manager(worker.id, 99999)
    session.close()


def test_default_workforce_receives_canonical_identities(tmp_path):
    from app.employees.employee_service import EmployeeService
    from app.database.models import Employee, UserIdentity

    db = DatabaseManager(str(tmp_path / "workforce-identities.db"))
    db.initialize()
    session = db.get_session()

    EmployeeService(session).ensure_default_workforce()

    employees = session.query(Employee).all()
    identities = session.query(UserIdentity).filter(UserIdentity.employee_id.is_not(None)).all()

    assert len(employees) == len(identities) == len(EmployeeService.DEFAULT_EMPLOYEES)
    assert len({identity.employee_id for identity in identities}) == len(employees)

    john = session.query(Employee).filter_by(name="John Cho").one()
    john_identity = session.query(UserIdentity).filter_by(employee_id=john.id).one()
    assert john_identity.identity_type == "human"
    assert john_identity.email == "john@atlas.local"

    researcher = session.query(Employee).filter_by(name="Ava Chen").one()
    researcher_identity = session.query(UserIdentity).filter_by(employee_id=researcher.id).one()
    assert researcher_identity.identity_type == "ai_employee"
    assert researcher_identity.system_name == "ava-chen"
    assert researcher_identity.manager_id is not None
    session.close()


def test_workforce_identity_sync_is_idempotent(tmp_path):
    from app.employees.employee_service import EmployeeService
    from app.database.models import UserIdentity

    db = DatabaseManager(str(tmp_path / "workforce-idempotent.db"))
    db.initialize()
    session = db.get_session()
    employee_service = EmployeeService(session)

    employee_service.ensure_default_workforce()
    first_count = session.query(UserIdentity).count()
    employee_service.ensure_default_workforce()

    assert session.query(UserIdentity).count() == first_count
    session.close()
