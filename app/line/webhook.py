import base64
import hashlib
import hmac
from typing import Any

from app.agents.mimir import MimirAgent
from app.line.client import LineClient
from app.schemas import ChatRequest


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

        if not reply_token:
            ignored += 1
            continue

        if message.get("type") != "text":
            await line_client.reply_text(
                reply_token,
                "Mimir received it. For now this prototype supports LINE text messages only.",
            )
            handled += 1
            continue

        chat_request = ChatRequest(
            message=message.get("text", ""),
            user_id=user_id,
            conversation_id=f"line:{user_id}",
        )
        agent_response = await mimir.respond(chat_request)
        await line_client.reply_text(reply_token, agent_response.reply)
        handled += 1

    return {"ok": True, "handled": handled, "ignored": ignored}
