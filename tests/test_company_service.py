from app.core.company.models import Company, Department, Team


def test_company_defaults():
    company = Company(
        id=1,
        name="Atlas Intelligence",
    )

    assert company.name == "Atlas Intelligence"
    assert company.status == "active"
    assert company.timezone == "America/New_York"
    assert company.currency == "USD"
    assert company.settings == {}


def test_department_creation():
    department = Department(
        id=1,
        company_id=1,
        name="Engineering",
        code="engineering",
    )

    assert department.company_id == 1
    assert department.name == "Engineering"
    assert department.code == "engineering"
    assert department.status == "active"


def test_team_creation():
    team = Team(
        id=1,
        company_id=1,
        department_id=1,
        name="Platform Engineering",
        code="platform-engineering",
    )

    assert team.company_id == 1
    assert team.department_id == 1
    assert team.status == "active"