from collections.abc import Iterable

from app.agents.base import AgentProfile, SpecialistAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, SpecialistAgent] = {}
        self._profiles: dict[str, AgentProfile] = {}

    def register(
        self,
        profile: AgentProfile,
        agent: SpecialistAgent,
    ) -> None:
        self._profiles[profile.id] = profile
        self._agents[profile.id] = agent

    def get(self, agent_id: str) -> SpecialistAgent | None:
        return self._agents.get(agent_id)

    def profile(self, agent_id: str) -> AgentProfile | None:
        return self._profiles.get(agent_id)

    def profiles(self) -> tuple[AgentProfile, ...]:
        return tuple(self._profiles.values())

    def enabled_agent_names(self) -> list[str]:
        return [profile.name for profile in self.profiles()]

    def match(self, message: str) -> str | None:
        normalized = message.lower()
        matches: list[tuple[int, str]] = []
        for profile in self.profiles():
            score = sum(
                max(1, len(keyword.split()))
                for keyword in profile.keywords
                if keyword in normalized
            )
            if score:
                matches.append((score, profile.id))
        if not matches:
            return None
        matches.sort(reverse=True)
        return matches[0][1]

    def extend(
        self,
        entries: Iterable[tuple[AgentProfile, SpecialistAgent]],
    ) -> None:
        for profile, agent in entries:
            self.register(profile, agent)
