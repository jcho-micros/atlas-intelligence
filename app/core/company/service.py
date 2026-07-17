from __future__ import annotations

import re

from sqlalchemy.orm import Session

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
from app.database.models import (
    Organization,
    OrganizationDepartment,
    OrganizationTeam,
)


def normalize_code(value: str) -> str:
    """Normalize a department or team code."""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").upper()

    if not normalized:
        raise ValueError("Code cannot be empty.")

    return normalized


class CompanyService:
    """Application service for organizations, departments, and teams."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_company(self, organization_id: int) -> Organization:
        company = self.session.get(Organization, organization_id)

        if company is None:
            raise CompanyNotFound(
                f"Organization {organization_id} was not found."
            )

        return company

    def create_department(
        self,
        organization_id: int,
        name: str,
        code: str,
        description: str | None = None,
        status: str = "active",
    ) -> OrganizationDepartment:
        self.get_company(organization_id)

        clean_name = name.strip()
        clean_code = normalize_code(code)

        if not clean_name:
            raise InvalidDepartment("Department name cannot be empty.")

        existing = (
            self.session.query(OrganizationDepartment)
            .filter(
                OrganizationDepartment.organization_id == organization_id,
                OrganizationDepartment.code == clean_code,
            )
            .first()
        )

        if existing is not None:
            raise DuplicateDepartment(
                f"Department code {clean_code} already exists."
            )

        department = OrganizationDepartment(
            organization_id=organization_id,
            name=clean_name,
            code=clean_code,
            description=description,
            status=status,
        )

        self.session.add(department)
        self.session.flush()

        return department

    def get_department(self, department_id: int) -> OrganizationDepartment:
        department = self.session.get(OrganizationDepartment, department_id)

        if department is None:
            raise DepartmentNotFound(
                f"Department {department_id} was not found."
            )

        return department

    def create_team(
        self,
        organization_id: int,
        department_id: int,
        name: str,
        code: str,
        description: str | None = None,
        status: str = "active",
    ) -> OrganizationTeam:
        self.get_company(organization_id)
        department = self.get_department(department_id)

        if department.organization_id != organization_id:
            raise InvalidTeam(
                "The department does not belong to this organization."
            )

        clean_name = name.strip()
        clean_code = normalize_code(code)

        if not clean_name:
            raise InvalidTeam("Team name cannot be empty.")

        existing = (
            self.session.query(OrganizationTeam)
            .filter(
                OrganizationTeam.organization_id == organization_id,
                OrganizationTeam.code == clean_code,
            )
            .first()
        )

        if existing is not None:
            raise DuplicateTeam(
                f"Team code {clean_code} already exists."
            )

        team = OrganizationTeam(
            organization_id=organization_id,
            department_id=department_id,
            name=clean_name,
            code=clean_code,
            description=description,
            status=status,
        )

        self.session.add(team)
        self.session.flush()

        return team

    def get_team(self, team_id: int) -> OrganizationTeam:
        team = self.session.get(OrganizationTeam, team_id)

        if team is None:
            raise TeamNotFound(f"Team {team_id} was not found.")

        return team

    def update_company(
        self,
        organization_id: int,
        **updates: object,
    ) -> Organization:
        company = self.get_company(organization_id)

        allowed_fields = {
            "name",
            "slug",
            "status",
            "timezone",
            "settings_json",
        }

        invalid_fields = set(updates) - allowed_fields

        if invalid_fields:
            raise InvalidCompanyUpdate(
                f"Unsupported fields: {sorted(invalid_fields)}"
            )

        for field, value in updates.items():
            setattr(company, field, value)

        self.session.flush()

        return company
