from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from app.core.company.exceptions import (
    CompanyNotFound,
    DuplicateDepartment,
    DuplicateTeam,
    InvalidCompanyUpdate,
    InvalidDepartment,
    InvalidTeam,
)
from app.core.company.service import CompanyService
from app.database.models import (
    Organization,
    OrganizationDepartment,
    OrganizationTeam,
)


def _get_or_create_company(session: Session) -> Organization:
    """Return Atlas's primary organization, creating it when needed."""
    company = (
        session.query(Organization)
        .order_by(Organization.id.asc())
        .first()
    )

    if company is not None:
        return company

    company = Organization(
        name="Atlas Intelligence",
        slug="atlas-intelligence",
        status="active",
        timezone="America/New_York",
    )
    session.add(company)
    session.commit()
    session.refresh(company)

    return company


def _load_departments(
    session: Session,
    organization_id: int,
) -> list[OrganizationDepartment]:
    return (
        session.query(OrganizationDepartment)
        .filter(
            OrganizationDepartment.organization_id == organization_id
        )
        .order_by(OrganizationDepartment.name.asc())
        .all()
    )


def _load_teams(
    session: Session,
    organization_id: int,
) -> list[OrganizationTeam]:
    return (
        session.query(OrganizationTeam)
        .filter(
            OrganizationTeam.organization_id == organization_id
        )
        .order_by(OrganizationTeam.name.asc())
        .all()
    )


def _organization_form(
    session: Session,
    company: Organization,
) -> None:
    service = CompanyService(session)

    st.subheader("Organization")
    st.caption("Manage the primary company record used by Atlas Enterprise.")

    with st.form("organization_form"):
        left, right = st.columns(2)

        with left:
            name = st.text_input(
                "Organization name",
                value=company.name or "",
            )
            slug = st.text_input(
                "Slug",
                value=company.slug or "",
            )

        with right:
            timezone = st.text_input(
                "Timezone",
                value=company.timezone or "America/New_York",
            )
            status_options = ["active", "inactive"]
            current_status = str(company.status or "active").lower()

            status = st.selectbox(
                "Status",
                status_options,
                index=(
                    status_options.index(current_status)
                    if current_status in status_options
                    else 0
                ),
            )

        submitted = st.form_submit_button(
            "Save organization",
            type="primary",
        )

    if not submitted:
        return

    try:
        service.update_company(
            company.id,
            name=name.strip(),
            slug=slug.strip(),
            timezone=timezone.strip(),
            status=status,
        )
        session.commit()
        st.success("Organization updated.")
        st.rerun()
    except (CompanyNotFound, InvalidCompanyUpdate, ValueError) as exc:
        session.rollback()
        st.error(str(exc))
    except Exception as exc:
        session.rollback()
        st.error(f"Unable to update organization: {exc}")


def _department_form(
    session: Session,
    company: Organization,
) -> None:
    service = CompanyService(session)

    with st.expander("Add department", expanded=False):
        with st.form("create_department_form", clear_on_submit=True):
            name = st.text_input(
                "Department name",
                placeholder="Engineering",
            )
            code = st.text_input(
                "Department code",
                placeholder="engineering",
                help="Codes are normalized automatically.",
            )
            description = st.text_area(
                "Description",
                placeholder="Builds and maintains the Atlas platform.",
            )
            status = st.selectbox(
                "Department status",
                ["active", "inactive"],
            )

            submitted = st.form_submit_button(
                "Create department",
                type="primary",
            )

        if not submitted:
            return

        try:
            service.create_department(
                organization_id=company.id,
                name=name,
                code=code,
                description=description.strip() or None,
                status=status,
            )
            session.commit()
            st.success(f"Department '{name.strip()}' created.")
            st.rerun()
        except (
            DuplicateDepartment,
            InvalidDepartment,
            CompanyNotFound,
            ValueError,
        ) as exc:
            session.rollback()
            st.error(str(exc))
        except Exception as exc:
            session.rollback()
            st.error(f"Unable to create department: {exc}")


def _team_form(
    session: Session,
    company: Organization,
    departments: list[OrganizationDepartment],
) -> None:
    if not departments:
        st.info("Create a department before adding teams.")
        return

    service = CompanyService(session)
    department_by_name = {
        department.name: department
        for department in departments
    }

    with st.expander("Add team", expanded=False):
        with st.form("create_team_form", clear_on_submit=True):
            department_name = st.selectbox(
                "Department",
                list(department_by_name.keys()),
            )
            name = st.text_input(
                "Team name",
                placeholder="Platform",
            )
            code = st.text_input(
                "Team code",
                placeholder="platform",
                help="Codes are normalized automatically.",
            )
            description = st.text_area(
                "Description",
                placeholder="Builds Atlas's core application platform.",
            )
            status = st.selectbox(
                "Team status",
                ["active", "inactive"],
            )

            submitted = st.form_submit_button(
                "Create team",
                type="primary",
            )

        if not submitted:
            return

        department = department_by_name[department_name]

        try:
            service.create_team(
                organization_id=company.id,
                department_id=department.id,
                name=name,
                code=code,
                description=description.strip() or None,
                status=status,
            )
            session.commit()
            st.success(f"Team '{name.strip()}' created.")
            st.rerun()
        except (
            DuplicateTeam,
            InvalidTeam,
            CompanyNotFound,
            ValueError,
        ) as exc:
            session.rollback()
            st.error(str(exc))
        except Exception as exc:
            session.rollback()
            st.error(f"Unable to create team: {exc}")


def _render_structure(
    departments: list[OrganizationDepartment],
    teams: list[OrganizationTeam],
) -> None:
    st.subheader("Company Structure")

    if not departments:
        st.info("No organization departments have been created yet.")
        return

    teams_by_department: dict[int, list[OrganizationTeam]] = {}

    for team in teams:
        teams_by_department.setdefault(team.department_id, []).append(team)

    for department in departments:
        department_teams = teams_by_department.get(department.id, [])

        with st.container(border=True):
            heading, metrics = st.columns([4, 1])

            with heading:
                st.markdown(f"### {department.name}")
                st.caption(
                    f"{department.code} · "
                    f"{str(department.status).title()}"
                )

                if department.description:
                    st.write(department.description)

            with metrics:
                st.metric("Teams", len(department_teams))

            if not department_teams:
                st.caption("No teams assigned to this department.")
                continue

            team_columns = st.columns(min(3, len(department_teams)))

            for index, team in enumerate(department_teams):
                with team_columns[index % len(team_columns)]:
                    with st.container(border=True):
                        st.markdown(f"**{team.name}**")
                        st.caption(
                            f"{team.code} · "
                            f"{str(team.status).title()}"
                        )

                        if team.description:
                            st.write(team.description)


def render_company_management(session: Session) -> None:
    """Render organization, department, and team administration."""
    company = _get_or_create_company(session)
    departments = _load_departments(session, company.id)
    teams = _load_teams(session, company.id)

    st.header("Company Management")
    st.caption(
        "Manage the organization structure used by Atlas Enterprise."
    )

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Organization", company.name)
    metric_2.metric("Departments", len(departments))
    metric_3.metric("Teams", len(teams))
    metric_4.metric("Status", str(company.status).title())

    st.divider()

    organization_tab, departments_tab, teams_tab = st.tabs(
        ["Organization", "Departments", "Teams"]
    )

    with organization_tab:
        _organization_form(session, company)

    with departments_tab:
        _department_form(session, company)
        st.divider()
        _render_structure(departments, teams)

    with teams_tab:
        _team_form(session, company, departments)
        st.divider()
        _render_structure(departments, teams)
