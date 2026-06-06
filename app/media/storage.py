from pathlib import Path
from uuid import uuid4

from app.media.models import MediaAttachment


class TemporaryMediaStorage:
    def __init__(self, root_dir: str = "/tmp/mimir_media") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, mime_type: str, source: str) -> MediaAttachment:
        suffix = _suffix_for_mime_type(mime_type)
        path = self.root_dir / f"{uuid4().hex}{suffix}"
        path.write_bytes(content)
        return MediaAttachment(path=path, mime_type=mime_type, source=source)

    def delete(self, attachment: MediaAttachment) -> None:
        attachment.path.unlink(missing_ok=True)


def _suffix_for_mime_type(mime_type: str) -> str:
    if mime_type == "image/png":
        return ".png"
    if mime_type == "image/webp":
        return ".webp"
    return ".jpg"

