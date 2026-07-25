# character.py
from pydantic import BaseModel

class Character(BaseModel):
    id: str # veritabanlari icin arkaplanda id. hikaye ile alakasiz.
    name: str # karakterin kullanilan ismi
    full_name: str # karakterin tam adi
    age: str
    role: str # karakterin rolu ve onem derecesi: mesela bilmemnerenin krali ve ana karakter gibi.
    physicality: str # karakterin fiziksel ozellikleri
    personality: str # karakterin kisisel ozellikleri
    speech_style: str
    relationships: dict[str, str]
    info: list[str] # karakter hakkinda diger bilgiler, esyalari, gecmisi, etc.
    experience: list[str] # burasi karakterin guncellemeleri. mesela chapter 5 de yeni bir asa edinmistir veya spor salonunda kas yapmistir veya psikolojisi bozulmustur gibi gibi

