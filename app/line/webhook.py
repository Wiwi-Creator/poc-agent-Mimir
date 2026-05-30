import base64
import hashlib
import hmac
import logging
from typing import Any

from app.agents.mimir import MimirAgent
from app.line.client import LineClient
from app.schemas import ChatRequest

logger = logging.getLogger(__name__)


class LineSignatureError(RuntimeError):
    pass


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> None:
    if not channel_secret:
        raise LineSignatureError("LINE_CHANNEL_SECRET is not configured.")
    if not signature:
        raise LineSignatureError("Missing X-Line-Signature header.")

    digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    if not hmac.compare_digest(expected_signature, signature):
        raise LineSignatureError("Invalid LINE signature.")


async def handle_line_events(
    payload: dict[str, Any],
    mimir: MimirAgent,
    line_client: LineClient,
    send_thinking_message: bool = True,
) -> dict[str, Any]:
    handled = 0
    ignored = 0

    for event in payload.get("events", []):
        if event.get("type") != "message":
            ignored += 1
            continue

        message = event.get("message", {})
        reply_token = event.get("replyToken")
        user_id = event.get("source", {}).get("userId", "line-user")
        mark_as_read_token = event.get("markAsReadToken")

        if not reply_token:
            ignored += 1
            continue

        if mark_as_read_token:
            await _try_mark_as_read(line_client, mark_as_read_token)
        else:
            logger.info("LINE message event did not include markAsReadToken")

        if message.get("type") != "text":
            await line_client.reply_text(
                reply_token,
                "Mimir received it. For now this prototype supports LINE text messages only.",
            )
            handled += 1
            continue

        await _try_start_loading(line_client, user_id)
        if send_thinking_message:
            await _try_push_thinking_message(line_client, user_id)

        chat_request = ChatRequest(
            message=message.get("text", ""),
            user_id=user_id,
            conversation_id=f"line:{user_id}",
        )
        agent_response = await mimir.respond(chat_request)
        await line_client.reply_text(reply_token, agent_response.reply)
        handled += 1

    return {"ok": True, "handled": handled, "ignored": ignored}


async def _try_start_loading(line_client: LineClient, user_id: str) -> None:
    try:
        await line_client.start_loading(user_id, loading_seconds=10)
        logger.info("Started LINE loading animation")
    except Exception:
        # Loading animation is best effort. LINE may reject it for groups,
        # blocked users, or clients that do not support the feature.
        logger.exception("Could not start LINE loading animation")
        return


async def _try_mark_as_read(line_client: LineClient, mark_as_read_token: str) -> None:
    try:
        await line_client.mark_as_read(mark_as_read_token)
        logger.info("Marked LINE message as read")
    except Exception:
        logger.exception("Could not mark LINE message as read")
        return


async def _try_push_thinking_message(line_client: LineClient, user_id: str) -> None:
    try:
        await line_client.push_text(user_id, "Mimir is thinking... Meow")
        logger.info("Pushed LINE thinking message")
    except Exception:
        logger.exception("Could not push LINE thinking message")
        return
