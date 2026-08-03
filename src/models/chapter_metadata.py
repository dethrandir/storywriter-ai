# chapter_metadata.py
from pydantic import BaseModel


class ChapterMeta(BaseModel):
    """Bölümün final meta verisi (başlık, açıklama, özet)."""
    title: str = ""
    description: str = ""
    summary: str = ""
