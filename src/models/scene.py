# scene.py
from pydantic import BaseModel
from src.models.setting import Setting

class Scene(BaseModel):
    """
    bir yazinin sahnesini tanimlar. bir chapterde birden fazla sahne olabilir. sahneler meta olaylar gibi tanimlanabilir.
    """
    id: str
    title: str # sahnenin basligi
    setting: str # sahnenin mekan & zamani
    characters: list[str]
    conflicts: list[str] # conflicts
    events: list[str] # event ids
