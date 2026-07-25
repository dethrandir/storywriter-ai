# world.py
from pydantic import BaseModel
class World(BaseModel):
    name: str # dunyanin/evrenin ismi
    id: str # uygulama backendi ve baglantilar icin id
    style: str # dunyanin tarzi
    summary: str # dunyanin genelgecer bilgisi
    lores: list[str]
    experience: list[str] # yine deneyimler
