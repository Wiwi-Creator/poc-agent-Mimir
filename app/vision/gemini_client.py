from pathlib import Path

from google import genai
from google.genai import types
from google.genai.types import HttpOptions


class GeminiVisionError(RuntimeError):
    pass


class GeminiVisionClient:
    def __init__(
        self,
        project: str,
        location: str,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.model = model
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=HttpOptions(api_version="v1"),
        )

    async def analyze_image(
        self,
        image_path: Path,
        mime_type: str,
        prompt: str,
    ) -> str:
        image_bytes = image_path.read_bytes()
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )
        except Exception as exc:
            raise GeminiVisionError(f"Gemini vision request failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise GeminiVisionError("Gemini vision returned an empty response.")
        return text.strip()

