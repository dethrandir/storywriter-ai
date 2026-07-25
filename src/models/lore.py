# lore.py
from pydantic import BaseModel

class Lore(BaseModel):
    id: str
    category: str # "rule", "history", "geography", "lore",
    title: str
    content: str
