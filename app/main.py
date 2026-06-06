from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.agents.mimir import MimirAgent
from app.config import Settings, get_settings
from app.dashboard import DASHBOARD_HTML
from app.line.client import LineClient, LineClientError
from app.line.webhook import (
    LineSignatureError,
    handle_line_events,
    verify_line_signature,
)
from app.llm.groq_client import GroqClient, GroqClientError
from app.media.storage import TemporaryMediaStorage
from app.memory.user_state_store import UserStateStore
from app.memory.workout_store import WorkoutStore
from app.planning.plan_store import WorkoutPlanStore
from app.schemas import AgentInfo, ChatRequest, ChatResponse, HealthResponse
from app.tools.hulk_tools import HulkToolRegistry
from app.vision.analyzer import HulkImageAnalyzer, PhysiqueVisionAnalyzer
from app.vision.gemini_client import GeminiVisionClient

app = FastAPI(
    title="Mimir Multi-Agent System",
    description="Mimir orchestrates workout, travel, finance, career, tech, and meeting agents.",
    version="0.2.0",
)


def get_mimir(settings: Settings = Depends(get_settings)) -> MimirAgent:
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        base_url=settings.groq_base_url,
    )
    workout_store = WorkoutStore(settings.workout_db_path)
    plan_store = WorkoutPlanStore(settings.workout_plan_db_path)
    user_state_store = UserStateStore(settings.user_state_db_path)
    hulk_tools = HulkToolRegistry()
    physique_analyzer = None
    image_analyzer = None
    if settings.google_cloud_project:
        gemini_client = GeminiVisionClient(
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            model=settings.gemini_vision_model,
        )
        physique_analyzer = PhysiqueVisionAnalyzer(gemini_client)
        image_analyzer = HulkImageAnalyzer(gemini_client)
    return MimirAgent(
        groq_client=groq_client,
        workout_store=workout_store,
        plan_store=plan_store,
        user_state_store=user_state_store,
        hulk_tools=hulk_tools,
        physique_analyzer=physique_analyzer,
        image_analyzer=image_analyzer,
    )


def get_line_client(settings: Settings = Depends(get_settings)) -> LineClient:
    return LineClient(
        channel_access_token=settings.line_channel_access_token,
        base_url=settings.line_api_base_url,
        data_base_url=settings.line_data_base_url,
    )


def get_media_storage(settings: Settings = Depends(get_settings)) -> TemporaryMediaStorage:
    return TemporaryMediaStorage(settings.media_tmp_dir)


@app.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        groq_model=settings.groq_model,
        groq_configured=bool(settings.groq_api_key),
        line_configured=bool(settings.line_channel_access_token),
        line_signature_verification_configured=bool(settings.line_channel_secret),
        vision_configured=bool(settings.google_cloud_project),
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents(mimir: MimirAgent = Depends(get_mimir)) -> list[AgentInfo]:
    return [
        AgentInfo(
            id=profile.id,
            name=profile.name,
            role=profile.role,
            description=profile.description,
            icon=profile.icon,
            color=profile.color,
            capabilities=list(profile.capabilities),
        )
        for profile in mimir.agent_profiles()
    ]


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
    media_storage: TemporaryMediaStorage = Depends(get_media_storage),
) -> dict[str, object]:
    body = await request.body()
    try:
        verify_line_signature(body, x_line_signature, settings.line_channel_secret)
        payload = await request.json()
        return await handle_line_events(
            payload,
            mimir,
            line_client,
            media_storage=media_storage,
            send_thinking_message=settings.line_send_thinking_message,
        )
    except LineSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except GroqClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LineClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
