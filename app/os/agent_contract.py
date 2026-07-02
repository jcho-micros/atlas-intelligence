from dataclasses import dataclass, field


@dataclass
class AgentContract:
    name: str
    department: str
    responsibilities: list[str]
    input_events: list[str] = field(default_factory=list)
    output_events: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
