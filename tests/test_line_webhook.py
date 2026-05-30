import base64
import hashlib
import hmac

import pytest

from app.line.webhook import LineSignatureError, handle_line_events, verify_line_signature


class FakeMimir:
    async def respond(self, request):
        class Response:
            reply = f"reply to {request.message}"

        return Response()


class FakeLineClient:
    def __init__(self):
        self.replies = []

    async def reply_text(self, reply_token, text):
        self.replies.append((reply_token, text))


def make_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_verify_line_signature_accepts_valid_signature():
    body = b'{"events":[]}'
    secret = "test-secret"
    signature = make_signature(body, secret)

    verify_line_signature(body, signature, secret)


def test_verify_line_signature_rejects_invalid_signature():
    with pytest.raises(LineSignatureError):
        verify_line_signature(b"{}", "bad-signature", "test-secret")


@pytest.mark.asyncio
async def test_handle_line_text_message_replies():
    line_client = FakeLineClient()
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"userId": "user-123"},
                "message": {"type": "text", "text": "bench 80kg"},
            }
        ]
    }

    result = await handle_line_events(payload, FakeMimir(), line_client)

    assert result == {"ok": True, "handled": 1, "ignored": 0}
    assert line_client.replies == [("reply-token", "reply to bench 80kg")]

