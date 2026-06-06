from app.media.models import MediaAttachment
from app.vision.analyzer import HulkImageAnalyzer, PhysiqueVisionAnalyzer


class FakeGeminiClient:
    def __init__(self):
        self.calls = []

    async def analyze_image(self, image_path, mime_type, prompt):
        self.calls.append((image_path, mime_type, prompt))
        return "Visual notes: test"


async def test_physique_analyzer_calls_gemini_with_context(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"image")
    attachment = MediaAttachment(
        path=image_path,
        mime_type="image/jpeg",
        source="test",
    )
    gemini_client = FakeGeminiClient()
    analyzer = PhysiqueVisionAnalyzer(gemini_client)

    result = await analyzer.analyze_physique(attachment, context="front photo")

    assert result == "Visual notes: test"
    assert gemini_client.calls[0][0] == image_path
    assert gemini_client.calls[0][1] == "image/jpeg"
    assert "front photo" in gemini_client.calls[0][2]


async def test_hulk_image_analyzer_uses_food_and_confirmation_prompt(tmp_path):
    image_path = tmp_path / "meal.jpg"
    image_path.write_bytes(b"image")
    attachment = MediaAttachment(
        path=image_path,
        mime_type="image/jpeg",
        source="test",
    )
    gemini_client = FakeGeminiClient()
    analyzer = HulkImageAnalyzer(gemini_client)

    result = await analyzer.analyze_image(attachment, context="lunch photo")

    assert result == "Visual notes: test"
    prompt = gemini_client.calls[0][2]
    assert "Food check:" in prompt
    assert "Please confirm:" in prompt
    assert "calories and macros as ranges" in prompt
    assert "lunch photo" in prompt
