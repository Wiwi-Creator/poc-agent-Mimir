import httpx


class LineClientError(RuntimeError):
    pass


class LineClient:
    def __init__(
        self,
        channel_access_token: str,
        base_url: str = "https://api.line.me/v2/bot",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.channel_access_token = channel_access_token
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def reply_text(self, reply_token: str, text: str) -> None:
        if not self.channel_access_token:
            raise LineClientError("LINE_CHANNEL_ACCESS_TOKEN is not configured.")

        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": text[:5000],
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/message/reply",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LineClientError(f"LINE API error: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise LineClientError(f"LINE request failed: {exc}") from exc

