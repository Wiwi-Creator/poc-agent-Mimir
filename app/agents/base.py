from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgentProfile:
    id: str
    name: str
    role: str
    description: str
    icon: str
    color: str
    capabilities: tuple[str, ...]
    keywords: tuple[str, ...]


class SpecialistAgent(Protocol):
    name: str

    async def respond(self, message: str, user_id: str = "local-user") -> str:
        ...
