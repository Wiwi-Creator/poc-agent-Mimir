from app.media.models import MediaAttachment
from app.vision.gemini_client import GeminiVisionClient
from app.vision.prompts import HULK_IMAGE_ANALYSIS_PROMPT, PHYSIQUE_ANALYSIS_PROMPT


class PhysiqueVisionAnalyzer:
    def __init__(self, gemini_client: GeminiVisionClient) -> None:
        self.gemini_client = gemini_client

    async def analyze_physique(
        self,
        attachment: MediaAttachment,
        context: str = "",
    ) -> str:
        prompt = PHYSIQUE_ANALYSIS_PROMPT
        if context:
            prompt = f"{prompt}\n\nUser context:\n{context}"
        return await self.gemini_client.analyze_image(
            image_path=attachment.path,
            mime_type=attachment.mime_type,
            prompt=prompt,
        )


class HulkImageAnalyzer:
    def __init__(self, gemini_client: GeminiVisionClient) -> None:
        self.gemini_client = gemini_client

    async def analyze_image(
        self,
        attachment: MediaAttachment,
        context: str = "",
    ) -> str:
        prompt = HULK_IMAGE_ANALYSIS_PROMPT
        if context:
            prompt = f"{prompt}\n\nUser context:\n{context}"
        return await self.gemini_client.analyze_image(
            image_path=attachment.path,
            mime_type=attachment.mime_type,
            prompt=prompt,
        )
