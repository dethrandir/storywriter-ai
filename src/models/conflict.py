# conflict.py
from pydantic import BaseModel

class Conflict(BaseModel):
    id: str # id
    description: str # catisma hakkinda bilgi
    effects: list[str] # neden oldugu degisimler etkiler
