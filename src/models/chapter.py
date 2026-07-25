# chapter.py
from pydantic import BaseModel

class Chapter(BaseModel):
    """
    Chapter
    Hikayenin / kitabin bir bolumudur. kitaba katilan kismi aslen basligi ve icerigidir.
    Diger kisimlar (summary, description etc.) author ve AI icindir.
    """
    id: str
    title: str # chapterin basligi
    description: str # chapterin aciklamasi
    summary: str # chapterin ozeti. sonraki chapterlerde kullanmak veya embedding icin guzel.
    scene_ids: list[str]
    content: str # sahnenin metni (sahneler vb. birlesmis)
