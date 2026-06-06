from pathlib import Path

from pydantic import BaseModel


class MediaAttachment(BaseModel):
    path: Path
    mime_type: str
    source: str

