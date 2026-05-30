from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_env: str
    groq_model: str
    groq_configured: bool


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = "local-user"
    conversation_id: str = "local"


class ChatResponse(BaseModel):
    agent: str
    route: Literal["hulk", "mimir"]
    reply: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
