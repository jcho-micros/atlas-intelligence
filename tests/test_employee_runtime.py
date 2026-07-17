def test_employee_runtime_imports():
    from app.employees.mind import EmployeeMind, MindDecision
    from app.employees.runtime_service import EmployeeRuntimeService

    assert EmployeeMind is not None
    assert MindDecision is not None
    assert EmployeeRuntimeService is not None
