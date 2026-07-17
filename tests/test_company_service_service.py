from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.company.exceptions import (
    CompanyNotFound,
    DepartmentNotFound,
    DuplicateDepartment,
    DuplicateTeam,
    InvalidCompanyUpdate,
    InvalidDepartment,
    InvalidTeam,
    TeamNotFound,
)
from app.core.company.service import CompanyService, normalize_code
from app.database.models import Base, Organization


@pytest.fixture()
def session() -> Session:
    """Create an isolated in-memory database for each test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    database_session = session_factory()

    try:
        yield database_session
    finally:
        database_session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def company(session: Session) -> Organization:
    organization = Organization(
        name="Atlas Intelligence",
        slug="atlas-intelligence",
    )

    session.add(organization)
    session.flush()

    return organization


@pytest.fixture()
def service(session: Session) -> CompanyService:
    return CompanyService(session)


def test_normalize_code():
    assert normalize_code("Product Design") == "PRODUCT_DESIGN"
    assert normalize_code(" platform-engineering ") == "PLATFORM_ENGINEERING"
    assert normalize_code("Sales & Marketing") == "SALES_MARKETING"


def test_normalize_code_rejects_empty_code():
    with pytest.raises(ValueError, match="Code cannot be empty"):
        normalize_code(" -- ")


def test_get_company(
    service: CompanyService,
    company: Organization,
):
    result = service.get_company(company.id)

    assert result.id == company.id
    assert result.name == "Atlas Intelligence"
    assert result.slug == "atlas-intelligence"


def test_get_company_not_found(service: CompanyService):
    with pytest.raises(
        CompanyNotFound,
        match="Organization 999 was not found",
    ):
        service.get_company(999)


def test_create_department(
    service: CompanyService,
    company: Organization,
):
    department = service.create_department(
        organization_id=company.id,
        name="  Product Design  ",
        code="product-design",
        description="Designs Atlas products.",
    )

    assert department.id is not None
    assert department.organization_id == company.id
    assert department.name == "Product Design"
    assert department.code == "PRODUCT_DESIGN"
    assert department.description == "Designs Atlas products."
    assert department.status == "active"


def test_create_department_rejects_empty_name(
    service: CompanyService,
    company: Organization,
):
    with pytest.raises(
        InvalidDepartment,
        match="Department name cannot be empty",
    ):
        service.create_department(
            organization_id=company.id,
            name="   ",
            code="engineering",
        )


def test_create_department_rejects_duplicate_code(
    service: CompanyService,
    company: Organization,
):
    service.create_department(
        organization_id=company.id,
        name="Product Design",
        code="product-design",
    )

    with pytest.raises(
        DuplicateDepartment,
        match="Department code PRODUCT_DESIGN already exists",
    ):
        service.create_department(
            organization_id=company.id,
            name="Another Product Department",
            code="Product Design",
        )


def test_create_department_requires_existing_company(
    service: CompanyService,
):
    with pytest.raises(
        CompanyNotFound,
        match="Organization 999 was not found",
    ):
        service.create_department(
            organization_id=999,
            name="Engineering",
            code="engineering",
        )


def test_get_department_not_found(service: CompanyService):
    with pytest.raises(
        DepartmentNotFound,
        match="Department 999 was not found",
    ):
        service.get_department(999)


def test_create_team(
    service: CompanyService,
    company: Organization,
):
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    team = service.create_team(
        organization_id=company.id,
        department_id=department.id,
        name="  Platform Engineering  ",
        code="platform-engineering",
        description="Builds the Atlas platform.",
    )

    assert team.id is not None
    assert team.organization_id == company.id
    assert team.department_id == department.id
    assert team.name == "Platform Engineering"
    assert team.code == "PLATFORM_ENGINEERING"
    assert team.description == "Builds the Atlas platform."
    assert team.status == "active"


def test_create_team_rejects_empty_name(
    service: CompanyService,
    company: Organization,
):
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    with pytest.raises(
        InvalidTeam,
        match="Team name cannot be empty",
    ):
        service.create_team(
            organization_id=company.id,
            department_id=department.id,
            name="   ",
            code="platform",
        )


def test_create_team_rejects_duplicate_code(
    service: CompanyService,
    company: Organization,
):
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    service.create_team(
        organization_id=company.id,
        department_id=department.id,
        name="Platform Engineering",
        code="platform-engineering",
    )

    with pytest.raises(
        DuplicateTeam,
        match="Team code PLATFORM_ENGINEERING already exists",
    ):
        service.create_team(
            organization_id=company.id,
            department_id=department.id,
            name="Another Platform Team",
            code="Platform Engineering",
        )


def test_create_team_rejects_department_from_another_company(
    session: Session,
    service: CompanyService,
    company: Organization,
):
    second_company = Organization(
        name="Second Company",
        slug="second-company",
    )

    session.add(second_company)
    session.flush()

    second_department = service.create_department(
        organization_id=second_company.id,
        name="Operations",
        code="operations",
    )

    with pytest.raises(
        InvalidTeam,
        match="department does not belong to this organization",
    ):
        service.create_team(
            organization_id=company.id,
            department_id=second_department.id,
            name="Platform",
            code="platform",
        )


def test_create_team_requires_existing_department(
    service: CompanyService,
    company: Organization,
):
    with pytest.raises(
        DepartmentNotFound,
        match="Department 999 was not found",
    ):
        service.create_team(
            organization_id=company.id,
            department_id=999,
            name="Platform",
            code="platform",
        )


def test_get_team_not_found(service: CompanyService):
    with pytest.raises(
        TeamNotFound,
        match="Team 999 was not found",
    ):
        service.get_team(999)


def test_update_company(
    service: CompanyService,
    company: Organization,
):
    updated_company = service.update_company(
        company.id,
        name="Atlas Enterprise",
        slug="atlas-enterprise",
        status="inactive",
        timezone="UTC",
        settings_json='{"mode": "enterprise"}',
    )

    assert updated_company.name == "Atlas Enterprise"
    assert updated_company.slug == "atlas-enterprise"
    assert updated_company.status == "inactive"
    assert updated_company.timezone == "UTC"
    assert updated_company.settings_json == '{"mode": "enterprise"}'


def test_update_company_rejects_unsupported_fields(
    service: CompanyService,
    company: Organization,
):
    with pytest.raises(
        InvalidCompanyUpdate,
        match="Unsupported fields",
    ):
        service.update_company(
            company.id,
            created_at="not-allowed",
        )


def test_update_company_not_found(service: CompanyService):
    with pytest.raises(
        CompanyNotFound,
        match="Organization 999 was not found",
    ):
        service.update_company(
            999,
            name="Missing Company",
        )