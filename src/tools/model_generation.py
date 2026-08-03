# model_generation.py
"""
Model üretim aracı — agent'lar üzerinden model üreten ince bir katman.
"""
from typing import Any

from src.agents import edit, generate, generate_for_story
from src.models.character import Character
from src.models.conflict import Conflict
from src.models.event import Event
from src.models.lore import Lore
from src.models.setting import Setting
from src.models.world import World

_TYPE_TO_MODEL = {
    "character": Character,
    "world": World,
    "setting": Setting,
    "lore": Lore,
    "event": Event,
    "conflict": Conflict,
}


async def generate_model(
    model_type: str,
    prompt: str,
    *,
    context: str | None = None,
    collection: str | None = None,
) -> Any:
    """Sıfırdan (hikayeye bağlı kalmaksızın) model üretir."""
    return await generate(model_type, prompt, context=context, collection=collection)


async def generate_model_for_story(
    model_type: str,
    prompt: str,
    *,
    context: str | None = None,
    collection: str | None = None,
) -> Any:
    """Hikaye bağlamına uygun model üretir."""
    return await generate_for_story(model_type, prompt, context=context, collection=collection)


async def edit_model(
    model_type: str,
    prompt: str,
    *,
    partial_data: dict[str, Any],
    context: str | None = None,
    collection: str | None = None,
) -> Any:
    """Mevcut model verisini prompt'a göre düzenler."""
    return await edit(
        model_type, prompt, partial_data=partial_data, context=context, collection=collection
    )
