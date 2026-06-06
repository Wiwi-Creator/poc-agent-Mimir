import base64
import hashlib
import hmac

import pytest

from app.line.webhook import LineSignatureError, handle_line_events, verify_line_signature


class FakeMimir:
    def route(self, message):
        return "hulk" if "bench" in message.lower() else "mimir"

    async def respond(self, request):
        class Response:
            reply = f"reply to {request.message}"

        return Response()

    async def respond_to_image(self, attachment, user_id, context=""):
        class Response:
            reply = f"image reply from {attachment.source}"

        return Response()


class FakeLineClient:
    def __init__(self):
        self.replies = []
        self.loading = []
        self.read_tokens = []
        self.pushes = []
        self.downloaded = []

    async def start_loading(self, chat_id, loading_seconds=10):
        self.loading.append((chat_id, loading_seconds))

    async def mark_as_read(self, mark_as_read_token):
        self.read_tokens.append(mark_as_read_token)

    async def reply_text(self, reply_token, text):
        self.replies.append((reply_token, text))

    async def push_text(self, user_id, text):
        self.pushes.append((user_id, text))

    async def get_message_content(self, message_id):
        self.downloaded.append(message_id)
        return b"image-bytes", "image/jpeg"


class FakeMediaStorage:
    def __init__(self):
        self.saved = []
        self.deleted = []

    def save(self, content, mime_type, source):
        from pathlib import Path

        from app.media.models import MediaAttachment

        attachment = MediaAttachment(
            path=Path("/tmp/fake-image.jpg"),
            mime_type=mime_type,
            source=source,
        )
        self.saved.append((content, mime_type, source, attachment))
        return attachment

    def delete(self, attachment):
        self.deleted.append(attachment)


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
                "markAsReadToken": "read-token",
                "source": {"userId": "user-123"},
                "message": {"type": "text", "text": "bench 80kg"},
            }
        ]
    }

    result = await handle_line_events(payload, FakeMimir(), line_client)

    assert result == {"ok": True, "handled": 1, "ignored": 0}
    assert line_client.read_tokens == ["read-token"]
    assert line_client.loading == [("user-123", 10)]
    assert line_client.pushes == [
        ("user-123", "🐈 Meow ~ (Mimir is thinking)"),
        ("user-123", "go through Hulk 🟢💪"),
    ]
    assert line_client.replies == [("reply-token", "reply to bench 80kg")]


@pytest.mark.asyncio
async def test_handle_line_text_message_can_skip_visible_thinking_message():
    line_client = FakeLineClient()
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"userId": "user-123"},
                "message": {"type": "text", "text": "hello"},
            }
        ]
    }

    result = await handle_line_events(
        payload,
        FakeMimir(),
        line_client,
        send_thinking_message=False,
    )

    assert result == {"ok": True, "handled": 1, "ignored": 0}
    assert line_client.loading == [("user-123", 10)]
    assert line_client.pushes == []
    assert line_client.replies == [("reply-token", "reply to hello")]


@pytest.mark.asyncio
async def test_handle_line_image_message_downloads_and_analyzes_physique():
    line_client = FakeLineClient()
    media_storage = FakeMediaStorage()
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"userId": "user-123"},
                "message": {"type": "image", "id": "image-message-id"},
            }
        ]
    }

    result = await handle_line_events(
        payload,
        FakeMimir(),
        line_client,
        media_storage=media_storage,
    )

    assert result == {"ok": True, "handled": 1, "ignored": 0}
    assert line_client.downloaded == ["image-message-id"]
    assert line_client.pushes == [
        ("user-123", "🐈 Meow ~ (Mimir is thinking)"),
        ("user-123", "go through Hulk 🟢💪"),
    ]
    assert media_storage.saved[0][0] == b"image-bytes"
    assert media_storage.saved[0][1] == "image/jpeg"
    assert media_storage.saved[0][2] == "line:image-message-id"
    assert media_storage.deleted == [media_storage.saved[0][3]]
    assert line_client.replies == [
        ("reply-token", "image reply from line:image-message-id")
    ]


@pytest.mark.asyncio
async def test_handle_line_image_message_replies_with_fallback_on_failure():
    class BrokenLineClient(FakeLineClient):
        async def get_message_content(self, message_id):
            raise RuntimeError("download failed")

    line_client = BrokenLineClient()
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"userId": "user-123"},
                "message": {"type": "image", "id": "image-message-id"},
            }
        ]
    }

    result = await handle_line_events(
        payload,
        FakeMimir(),
        line_client,
        media_storage=FakeMediaStorage(),
    )

    assert result == {"ok": True, "handled": 1, "ignored": 0}
    assert "I received your photo" in line_client.replies[0][1]
