from fastapi import Depends, FastAPI, HTTPException

from app.agents.mimir import MimirAgent
from app.config import Settings, get_settings
from app.llm.groq_client import GroqClient, GroqClientError
from app.schemas import ChatRequest, ChatResponse, HealthResponse

app = FastAPI(
    title="Mimir Local Prototype",
    description="Local FastAPI prototype for Mimir and the Hulk sub-agent.",
    version="0.1.0",
)


def get_mimir(settings: Settings = Depends(get_settings)) -> MimirAgent:
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
    )
    return MimirAgent(groq_client=groq_client)


@app.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        groq_model=settings.groq_model,
        groq_configured=bool(settings.groq_api_key),
    )


@app.post("/debug/chat", response_model=ChatResponse)
async def debug_chat(
    request: ChatRequest,
    mimir: MimirAgent = Depends(get_mimir),
) -> ChatResponse:
    try:
        return await mimir.respond(request)
    except GroqClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
