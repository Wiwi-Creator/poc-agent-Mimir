from fastapi import Depends, FastAPI, Header, HTTPException, Request

from app.agents.mimir import MimirAgent
from app.config import Settings, get_settings
from app.line.client import LineClient, LineClientError
from app.line.webhook import (
    LineSignatureError,
    handle_line_events,
    verify_line_signature,
)
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


def get_line_client(settings: Settings = Depends(get_settings)) -> LineClient:
    return LineClient(channel_access_token=settings.line_channel_access_token)


@app.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        groq_model=settings.groq_model,
        groq_configured=bool(settings.groq_api_key),
        line_configured=bool(settings.line_channel_access_token),
        line_signature_verification_configured=bool(settings.line_channel_secret),
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


@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    mimir: MimirAgent = Depends(get_mimir),
    line_client: LineClient = Depends(get_line_client),
) -> dict[str, object]:
    body = await request.body()
    try:
        verify_line_signature(body, x_line_signature, settings.line_channel_secret)
        payload = await request.json()
        return await handle_line_events(
            payload,
            mimir,
            line_client,
            send_thinking_message=settings.line_send_thinking_message,
        )
    except LineSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except GroqClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LineClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
