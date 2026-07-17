from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgentSkill:
    name: str
    description: str


class AtlasAgent(Protocol):
    name: str
    skills: list[AgentSkill]

    def can_handle(self, skill_name: str) -> bool:
        ...
