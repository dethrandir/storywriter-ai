# story_metadata.py
from pydantic import BaseModel

class StoryMetadata(BaseModel):
    id: str # veritabanlari icin hikaye idsi
    name: str # hikaye/kitap ismi
    authors: list[str] # yazarlar
    theme: str # hikayenin/kitabin genel temasi
    style_and_tone: str # yazarin uslubu, dili ve tarzi
    atmosphere: str # hikayenin genel atmosferi
    summary: str # hikayenin konusunun meta bir ozeti
