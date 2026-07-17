from app.employees.base_employee import BaseEmployee


class EmployeeRegistry:
    """In-memory registry for Atlas employees and their capabilities."""

    def __init__(self) -> None:
        self._employees: dict[str, BaseEmployee] = {}

    def register(self, employee: BaseEmployee) -> None:
        self._employees[employee.name.lower()] = employee

    def get(self, name: str) -> BaseEmployee | None:
        return self._employees.get(name.lower())

    def all(self) -> list[BaseEmployee]:
        return list(self._employees.values())

    def employees_with_skill(self, skill: str) -> list[BaseEmployee]:
        return [employee for employee in self._employees.values() if employee.can_perform(skill)]
