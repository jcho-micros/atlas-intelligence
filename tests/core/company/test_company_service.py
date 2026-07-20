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
    """Provide an isolated in-memory database for each test."""
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


def test_normalize_code() -> None:
    assert normalize_code("  Product Design  ") == "PRODUCT_DESIGN"
    assert normalize_code("sales-and marketing") == "SALES_AND_MARKETING"


def test_normalize_code_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="Code cannot be empty"):
        normalize_code(" -- ")


def test_get_company_returns_company(
    service: CompanyService,
    company: Organization,
) -> None:
    result = service.get_company(company.id)

    assert result.id == company.id
    assert result.name == "Atlas Intelligence"


def test_get_company_raises_when_missing(service: CompanyService) -> None:
    with pytest.raises(CompanyNotFound, match="Organization 999 was not found"):
        service.get_company(999)


def test_create_department_normalizes_values(
    service: CompanyService,
    company: Organization,
) -> None:
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
) -> None:
    with pytest.raises(
        InvalidDepartment,
        match="Department name cannot be empty",
    ):
        service.create_department(
            organization_id=company.id,
            name="   ",
            code="operations",
        )


def test_create_department_rejects_duplicate_code(
    service: CompanyService,
    company: Organization,
) -> None:
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
            name="Another Department",
            code="Product Design",
        )


def test_get_department_raises_when_missing(
    service: CompanyService,
) -> None:
    with pytest.raises(
        DepartmentNotFound,
        match="Department 999 was not found",
    ):
        service.get_department(999)


def test_create_team(
    service: CompanyService,
    company: Organization,
) -> None:
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    team = service.create_team(
        organization_id=company.id,
        department_id=department.id,
        name="  Platform Team  ",
        code="platform-team",
        description="Builds the Atlas platform.",
    )

    assert team.id is not None
    assert team.organization_id == company.id
    assert team.department_id == department.id
    assert team.name == "Platform Team"
    assert team.code == "PLATFORM_TEAM"
    assert team.description == "Builds the Atlas platform."
    assert team.status == "active"


def test_create_team_rejects_department_from_another_company(
    session: Session,
    service: CompanyService,
    company: Organization,
) -> None:
    second_company = Organization(
        name="Second Company",
        slug="second-company",
    )
    session.add(second_company)
    session.flush()

    department = service.create_department(
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
            department_id=department.id,
            name="Platform",
            code="platform",
        )


def test_create_team_rejects_empty_name(
    service: CompanyService,
    company: Organization,
) -> None:
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    with pytest.raises(InvalidTeam, match="Team name cannot be empty"):
        service.create_team(
            organization_id=company.id,
            department_id=department.id,
            name=" ",
            code="platform",
        )


def test_create_team_rejects_duplicate_code(
    service: CompanyService,
    company: Organization,
) -> None:
    department = service.create_department(
        organization_id=company.id,
        name="Engineering",
        code="engineering",
    )

    service.create_team(
        organization_id=company.id,
        department_id=department.id,
        name="Platform",
        code="platform-team",
    )

    with pytest.raises(
        DuplicateTeam,
        match="Team code PLATFORM_TEAM already exists",
    ):
        service.create_team(
            organization_id=company.id,
            department_id=department.id,
            name="Another Platform Team",
            code="Platform Team",
        )


def test_get_team_raises_when_missing(service: CompanyService) -> None:
    with pytest.raises(TeamNotFound, match="Team 999 was not found"):
        service.get_team(999)


def test_update_company(
    service: CompanyService,
    company: Organization,
) -> None:
    result = service.update_company(
        company.id,
        name="Atlas Enterprise",
        status="inactive",
        timezone="UTC",
    )

    assert result.name == "Atlas Enterprise"
    assert result.status == "inactive"
    assert result.timezone == "UTC"


def test_update_company_rejects_unsupported_fields(
    service: CompanyService,
    company: Organization,
) -> None:
    with pytest.raises(
        InvalidCompanyUpdate,
        match="Unsupported fields",
    ):
        service.update_company(
            company.id,
            created_at="not allowed",
        )
