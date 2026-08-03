# scene_plan.py
from pydantic import BaseModel


class ScenePlan(BaseModel):
    """
    Bir sahnenin planı. ChapterPlan içinde taşınır ve DB'de chapter_plans.scenes
    jsonb alanında saklanır. `summary` alanı sahnenin kısa durum anlatısıdır
    (chapter birleştirmesinde kullanılır).
    """
    id: str
    title: str = ""
    setting: str = ""  # setting id veya açıklama
    characters: list[str] = []
    conflicts: list[str] = []
    events: list[str] = []
    beats: list[str] = []  # sahne içindeki olay sırası (story beats)
    purpose: str = ""  # bu sahnenin bölüme katkısı
    summary: str = ""  # sahne özeti/durum anlatısı
    scene_exists: bool = False  # id mevcut bir Scene kaydına mı işaret ediyor (kullanıcı/üst AI'dan gelen)
    status: str = "planned"  # planned | drafted | revised | approved
