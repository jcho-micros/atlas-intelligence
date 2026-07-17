from app.database.manager import DatabaseManager
from app.database.models import EmployeeDecision, EmployeeGoal, EmployeeThought
from app.employees.employee_service import EmployeeService
from app.employees.runtime_service import EmployeeRuntimeService


def test_employee_mind_cycle_creates_thoughts_and_decisions(tmp_path):
    db_path = tmp_path / "atlas_test.db"
    db = DatabaseManager(str(db_path))
    db.initialize()
    session = db.get_session()
    try:
        EmployeeService(session).ensure_default_workforce()
        result = EmployeeRuntimeService(session).run_cycle(max_employees=3)
        assert result["employees_processed"] == 3
        assert session.query(EmployeeGoal).count() > 0
        assert session.query(EmployeeThought).count() > 0
        assert session.query(EmployeeDecision).count() > 0
    finally:
        session.close()
