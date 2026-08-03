# bundle.py
"""
Propagation tipleri: bir model üretimi/analizi sırasında ortaya çıkan ilişkili
değişiklikler (yeni varlıklar, deneyim güncellemeleri, bağlantılar).

- GenerationBundle: simple agents'ın `bundle=True` modunda döndürdüğü yapı
  (primary + related_creates + experience_updates + links).
- PropagationPlan: propagate_chapter'ın döndürdüğü yapı (primary yok).
"""
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.models.chapter import Chapter
from src.models.character import Character
from src.models.conflict import Conflict
from src.models.event import Event
from src.models.lore import Lore
from src.models.scene import Scene
from src.models.setting import Setting
from src.models.story import Story
from src.models.story_metadata import StoryMetadata
from src.models.world import World
from src.propagation.ops import ModelOp

RelatedEntityType = Literal[
    "character", "setting", "event", "conflict", "lore", "scene", "world", "chapter"
]

ENTITY_MODELS: dict[str, type[BaseModel]] = {
    "character": Character,
    "setting": Setting,
    "world": World,
    "lore": Lore,
    "event": Event,
    "conflict": Conflict,
    "scene": Scene,
    "chapter": Chapter,
    "story": Story,
    "story_metadata": StoryMetadata,
}

# Story kapsamında olan varlıklar: oluşturulurken story_id enjekte edilir
STORY_SCOPED = {"character", "setting", "event", "conflict", "scene"}


class RelatedCreate(BaseModel):
    entity_type: RelatedEntityType
    data: dict[str, Any]


class ExperienceUpdate(BaseModel):
    entity_type: Literal["character", "setting", "world"]
    entity_id: str
    note: str


class ModelLink(BaseModel):
    entity_type: str
    entity_id: str
    field: str
    value: str


class GenerationBundle(BaseModel):
    primary: dict[str, Any] = Field(default_factory=dict)
    related_creates: list[RelatedCreate] = Field(default_factory=list)
    experience_updates: list[ExperienceUpdate] = Field(default_factory=list)
    links: list[ModelLink] = Field(default_factory=list)


class PropagationPlan(BaseModel):
    related_creates: list[RelatedCreate] = Field(default_factory=list)
    experience_updates: list[ExperienceUpdate] = Field(default_factory=list)
    links: list[ModelLink] = Field(default_factory=list)


def _prepare_entity(
    entity_type: str,
    data: dict[str, Any],
    *,
    story_id: str | None = None,
) -> dict[str, Any]:
    """Entity verisini hazırlar: id üretir, story_id enjekte eder, şemaya göre doğrular."""
    data = dict(data or {})
    if not data.get("id"):
        data["id"] = str(uuid4())
    model = ENTITY_MODELS.get(entity_type)
    if model is not None:
        data = model.model_validate(data).model_dump(mode="json")
    # story_id pydantic modelinde olmadığından doğrulama sonrası tekrar eklenir
    if story_id and entity_type in STORY_SCOPED:
        data["story_id"] = story_id
    return data


def bundle_to_ops(
    model_type: str,
    bundle: GenerationBundle,
    *,
    story_id: str | None = None,
) -> list[ModelOp]:
    """GenerationBundle'ı uygulanabilir ModelOp listesine çevirir."""
    if model_type not in ENTITY_MODELS:
        raise ValueError(f"Bilinmeyen model tipi: {model_type}. Seçenekler: {list(ENTITY_MODELS)}")

    primary = _prepare_entity(model_type, bundle.primary, story_id=story_id)
    ops = [
        ModelOp(
            kind="create",
            entity_type=model_type,
            data=primary,
            note=f"{model_type} oluşturuldu",
        )
    ]
    for rc in bundle.related_creates:
        try:
            data = _prepare_entity(rc.entity_type, rc.data, story_id=story_id)
        except Exception as exc:
            ops.append(
                ModelOp(
                    kind="create",
                    entity_type=rc.entity_type,
                    data={},
                    note=f"İlişkili {rc.entity_type} atlandı (geçersiz): {exc}",
                )
            )
            continue
        ops.append(
            ModelOp(
                kind="create",
                entity_type=rc.entity_type,
                data=data,
                note=f"İlişkili {rc.entity_type} oluşturuldu",
            )
        )
    for eu in bundle.experience_updates:
        ops.append(
            ModelOp(
                kind="append_experience",
                entity_type=eu.entity_type,
                entity_id=eu.entity_id,
                data={"note": eu.note},
                note=f"{eu.entity_type} deneyim güncellendi",
            )
        )
    for link in bundle.links:
        ops.append(
            ModelOp(
                kind="append_to_array",
                entity_type=link.entity_type,
                entity_id=link.entity_id,
                field=link.field,
                data={"value": link.value},
                note=f"Bağlantı: {link.entity_type}.{link.field} ← {link.value}",
            )
        )
    return ops


def plan_to_ops(story_id: str, plan: PropagationPlan) -> tuple[list[ModelOp], list[str]]:
    """PropagationPlan'ı ModelOp listesine çevirir; geçersiz önerileri not eder."""
    ops: list[ModelOp] = []
    notes: list[str] = []

    for rc in plan.related_creates:
        try:
            data = _prepare_entity(rc.entity_type, rc.data, story_id=story_id)
        except Exception as exc:
            notes.append(f"İlişkili {rc.entity_type} atlandı (geçersiz): {exc}")
            continue
        ops.append(
            ModelOp(
                kind="create",
                entity_type=rc.entity_type,
                data=data,
                note=f"Yeni {rc.entity_type} oluşturuldu",
            )
        )
    for eu in plan.experience_updates:
        ops.append(
            ModelOp(
                kind="append_experience",
                entity_type=eu.entity_type,
                entity_id=eu.entity_id,
                data={"note": eu.note},
                note=f"{eu.entity_type} deneyim güncellendi: {eu.note[:80]}",
            )
        )
    for link in plan.links:
        ops.append(
            ModelOp(
                kind="append_to_array",
                entity_type=link.entity_type,
                entity_id=link.entity_id,
                field=link.field,
                data={"value": link.value},
                note=f"Bağlantı: {link.entity_type}.{link.field} ← {link.value}",
            )
        )
    return ops, notes
