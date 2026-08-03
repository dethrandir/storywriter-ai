# chapter_plan.py
from pydantic import BaseModel

from src.models.scene_plan import ScenePlan


class ChapterPlan(BaseModel):
    """
    Bir bölümün planı. Bölüm yazma pipeline'ının ilk artefaktıdır ve DB'de
    `chapter_plans` tablosunda saklanır (scenes jsonb olarak).
    Sahne-dışı anlatım kısımları `narration` listesinde tutulur; chapter'in
    illaki sahnelerden oluşması gerekmez.
    """
    id: str
    story_id: str
    index: int = 0  # hikayedeki bölüm sırası
    title: str = ""  # bölüm başlığı (plan + summarize aşaması)
    goal: str = ""  # bu bölümün amacı/ne başarılacak
    settings: list[str] = []
    characters: list[str] = []
    conflicts: list[str] = []
    events: list[str] = []
    scenes: list[ScenePlan] = []
    narration: list[str] = []  # sahne dışı anlatım bölümleri (açıklama)
    planned_summary: str = ""  # plan aşamasındaki özet taslağı
    description: str = ""  # bölüm açıklaması (UI/AI için)
    summary: str = ""  # bölüm özeti (UI + embedding + sonraki bölümler için)
    content: str = ""  # bölüm metni (düz yazı; pipeline sırasında taslak)
    status: str = "planned"  # planned | approved | drafting | done
