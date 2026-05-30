from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    name: str
    query: str
    content: str
    sources: list[str] = Field(default_factory=list)

