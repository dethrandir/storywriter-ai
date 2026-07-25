# event.py
from pydantic import BaseModel

class Event(BaseModel):
    id: str
    title: str # olayin adi, basligi
    description: str # olayin aciklamasi (yine embedding icin uygun
    date: str
    summary: str # olayin ozeti (embedding icin verimli)
    details: str # olayin detayli anlatimi
    characters: list[str]
    conflicts: list[str] # bu olayin yol actigi catismalar (mesela karaktere x ozelligi kazandirmasi veya engel olmasi veya geciktirmesi gibi
