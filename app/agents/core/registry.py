from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.core.base import AgentSkill


@dataclass
class RegisteredAgent:
    name: str
    department: str
    skills: list[AgentSkill] = field(default_factory=list)

    def can_handle(self, skill_name: str) -> bool:
        normalized = skill_name.lower().strip()
        return any(skill.name.lower().strip() == normalized for skill in self.skills)


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, RegisteredAgent] = {}

    def register(self, agent: RegisteredAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> RegisteredAgent | None:
        return self._agents.get(name)

    def all(self) -> list[RegisteredAgent]:
        return list(self._agents.values())

    def find_by_skill(self, skill_name: str) -> list[RegisteredAgent]:
        return [agent for agent in self._agents.values() if agent.can_handle(skill_name)]


def default_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        RegisteredAgent(
            name="Research Agent",
            department="Research",
            skills=[
                AgentSkill("analyze_market", "Analyze marketplace demand and competition."),
                AgentSkill("create_candidate", "Create candidate product projects."),
            ],
        )
    )
    registry.register(
        RegisteredAgent(
            name="Manufacturing Agent",
            department="Operations",
            skills=[
                AgentSkill("find_suppliers", "Find and compare supplier options."),
                AgentSkill("estimate_costs", "Estimate production and landed costs."),
            ],
        )
    )
    registry.register(
        RegisteredAgent(
            name="Finance Agent",
            department="Finance",
            skills=[
                AgentSkill("calculate_margin", "Calculate unit economics and margin."),
                AgentSkill("forecast_profit", "Forecast potential profit and ROI."),
            ],
        )
    )
    registry.register(
        RegisteredAgent(
            name="Marketing Agent",
            department="Marketing",
            skills=[
                AgentSkill("generate_seo", "Generate marketplace SEO and tags."),
                AgentSkill("create_launch_assets", "Create launch copy and content."),
            ],
        )
    )
    return registry
