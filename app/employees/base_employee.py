from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EmployeeBrief:
    name: str
    title: str
    department: str
    status: str
    current_task: str
    performance_score: float
    workload: float


@dataclass
class BaseEmployee:
    """Runtime representation of an Atlas AI employee.

    The database stores employee identity, memory, tools, and performance.
    This class is intentionally lightweight so future LLM-backed employees can
    inherit from one consistent interface.
    """

    name: str
    title: str
    department: str
    manager: str | None = None
    mission: str = ""
    personality: str = ""
    goals: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    status: str = "available"
    current_task: str = ""
    performance_score: float = 0.0
    workload: float = 0.0
    last_active_at: datetime = field(default_factory=datetime.utcnow)

    def brief(self) -> EmployeeBrief:
        return EmployeeBrief(
            name=self.name,
            title=self.title,
            department=self.department,
            status=self.status,
            current_task=self.current_task,
            performance_score=self.performance_score,
            workload=self.workload,
        )

    def can_perform(self, capability: str) -> bool:
        normalized = capability.lower().strip()
        return any(normalized in skill.lower() for skill in self.skills)

    def receive_task(self, task_title: str) -> None:
        self.current_task = task_title
        self.status = "working"
        self.last_active_at = datetime.utcnow()
