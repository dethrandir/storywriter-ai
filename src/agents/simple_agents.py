# simple_agents.py
"""
Basit modelleri üreten agent'lar.

Her model tipi için üç kullanım modu:
- generate:            sıfırdan, özgün üretim (hikayeye bağlı kalmak zorunda değil)
- generate_for_story:  verilen bağlama (dünya, lore, karakterler) uygun üretim
- edit:                mevcut modeli prompt'a göre düzenleme/tamamlama

Bağlam iki şekilde verilebilir:
- `context` ile doğrudan metin
- `collection` ile RAG (Qdrant) — verilirse prompt üzerinden otomatik çekilir

Örnek:
    await generate_for_story(
        "character",
        "Hikayeye yeni katılacak bir düşman generali",
        collection="story_123",
    )
"""
import json
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic_ai import Agent

from src.clients.ai import get_model
from src.models.character import Character
from src.models.conflict import Conflict
from src.models.event import Event
from src.models.lore import Lore
from src.models.setting import Setting
from src.models.world import World
from src.propagation import GenerationBundle, MutationResult, bundle_to_ops, execute
from src.utils.text import clean_model

SIMPLE_MODELS: dict[str, type[BaseModel]] = {
    "character": Character,
    "world": World,
    "setting": Setting,
    "lore": Lore,
    "event": Event,
    "conflict": Conflict,
}

LABELS: dict[str, str] = {
    "character": "karakter",
    "world": "dünya",
    "setting": "mekan/setting",
    "lore": "lore (bilgi/mit)",
    "event": "olay",
    "conflict": "çatışma",
}

BASE_SYSTEM_PROMPT = """
Sen bir worldbuilding ve hikaye tasarımı asistanısın. İstek doğrultusunda bir {label} oluşturur veya düzenlersin.

Kurallar:
- Çıktı her zaman istenen modelin şemasına (JSON schema) tam uygun olmalı; tüm zorunlu alanlar doldurulmalı.
- `id` alanı verilmişse aynen koru; verilmemişse UUID üret.
- Çıktıya hiçbir markdown/formatlama ekleme; yalnızca şemaya uygun veriyi döndür.
- Verilen hikaye bağlamıyla (dünya, lore, karakterler) tutarlı ol; çelişki yaratma.
- Alan içerikleri Türkçe, doğal ve hikayede kullanılabilir olmalı.
"""

MODE_SYSTEM_SUFFIX = {
    "generate": (
        "Sıfırdan, özgün bir {label} üret. Herhangi bir dünyaya veya hikayeye bağlı "
        "kalma zorunluluğu yok; tamamen yaratıcı olabilirsin."
    ),
    "generate_for_story": (
        "Aşağıda verilen hikaye bağlamına (dünya, lore, mevcut karakterler vb.) uygun "
        "ve onunla tutarlı bir {label} üret. Bağlamdaki bilgilerle çelişen şey üretme."
    ),
    "edit": (
        "Aşağıda verilen mevcut {label} verisini koru. İstenen değişiklikleri yap, "
        "belirtilmeyen alanları olduğu gibi muhafaza et ve eksik alanları mantıklı "
        "şekilde tamamla."
    ),
}

BUNDLE_SYSTEM_SUFFIX = """
Çıktı, istenen modelin verisini `primary` alanında içeren GenerationBundle olmalı.
Gerekli görürsen ilişkili modelleri `related_creates` ile öner (örn. bir event için çatışmalar).
Mevcut karakter/setting/world deneyimlerini güncellemek için `experience_updates` kullan
(id'ler bağlamdaki varlık dizininden alınır; dizin yoksa kullanma).
`primary.id` dahil tüm zorunlu alanları doldur.
"""

_agents: dict[tuple[str, str], Agent] = {}
_bundle_agents: dict[tuple[str, str], Agent] = {}


def _get_agent(model_type: str, mode: str) -> Agent:
    if model_type not in SIMPLE_MODELS:
        raise ValueError(
            f"Bilinmeyen model tipi: {model_type}. Seçenekler: {list(SIMPLE_MODELS)}"
        )
    if mode not in MODE_SYSTEM_SUFFIX:
        raise ValueError(f"Bilinmeyen mod: {mode}. Seçenekler: {list(MODE_SYSTEM_SUFFIX)}")

    key = (model_type, mode)
    if key not in _agents:
        _agents[key] = Agent(
            model=get_model(),
            system_prompt=(
                BASE_SYSTEM_PROMPT.format(label=LABELS[model_type])
                + "\n"
                + MODE_SYSTEM_SUFFIX[mode].format(label=LABELS[model_type])
            ),
            output_type=SIMPLE_MODELS[model_type],
        )
    return _agents[key]


def _get_bundle_agent(model_type: str, mode: str) -> Agent:
    if model_type not in SIMPLE_MODELS:
        raise ValueError(
            f"Bilinmeyen model tipi: {model_type}. Seçenekler: {list(SIMPLE_MODELS)}"
        )
    if mode not in MODE_SYSTEM_SUFFIX:
        raise ValueError(f"Bilinmeyen mod: {mode}. Seçenekler: {list(MODE_SYSTEM_SUFFIX)}")

    key = (model_type, mode)
    if key not in _bundle_agents:
        _bundle_agents[key] = Agent(
            model=get_model(),
            system_prompt=(
                BASE_SYSTEM_PROMPT.format(label=LABELS[model_type])
                + "\n"
                + MODE_SYSTEM_SUFFIX[mode].format(label=LABELS[model_type])
                + BUNDLE_SYSTEM_SUFFIX
            ),
            output_type=GenerationBundle,
        )
    return _bundle_agents[key]


async def _run(
    model_type: str,
    mode: str,
    prompt: str,
    *,
    context: str | None = None,
    collection: str | None = None,
    partial_data: dict[str, Any] | None = None,
    bundle: bool = False,
    auto: bool = True,
    story_id: str | None = None,
) -> BaseModel | MutationResult:
    if collection is not None:
        from src.clients.embeddings import get_context

        rag = await get_context(prompt, collection)
        if rag:
            context = "\n\n---\n\n".join(filter(None, [context, rag]))

    if story_id is not None:
        from src.propagation.context import entity_index

        index = await entity_index(story_id)
        if index:
            context = "\n\n---\n\n".join(filter(None, [context, f"Varlık dizini (id'ler):\n{index}"]))

    parts = [prompt]
    if context:
        parts.append(f"Hikaye bağlamı:\n{context}")
    if partial_data:
        parts.append(
            "Mevcut veri (korunacak/değiştirilecek):\n"
            + json.dumps(partial_data, ensure_ascii=False)
        )
    user_prompt = "\n\n".join(parts)

    if bundle:
        if mode == "edit":
            raise ValueError("bundle modu yalnızca generate/generate_for_story ile kullanılabilir.")
        result = await _get_bundle_agent(model_type, mode).run(user_prompt)
        generated: GenerationBundle = clean_model(result.data)
        if not generated.primary.get("id"):
            generated.primary["id"] = str(uuid4())
        ops = bundle_to_ops(model_type, generated, story_id=story_id)
        return await execute(ops, auto)

    result = await _get_agent(model_type, mode).run(user_prompt)

    if partial_data and partial_data.get("id"):
        result.data.id = partial_data["id"]
    else:
        result.data.id = str(uuid4())
    return result.data


async def generate(
    model_type: str,
    prompt: str,
    *,
    context: str | None = None,
    collection: str | None = None,
    bundle: bool = False,
    auto: bool = True,
    story_id: str | None = None,
) -> BaseModel | MutationResult:
    """Sıfırdan, özgün bir {model_type} üretir (hikayeye bağlı kalmak zorunda değil)."""
    return await _run(
        model_type,
        "generate",
        prompt,
        context=context,
        collection=collection,
        bundle=bundle,
        auto=auto,
        story_id=story_id,
    )


async def generate_for_story(
    model_type: str,
    prompt: str,
    *,
    context: str | None = None,
    collection: str | None = None,
    story_id: str | None = None,
    bundle: bool = False,
    auto: bool = True,
) -> BaseModel | MutationResult:
    """Verilen hikaye bağlamına (dünya, lore, karakterler) uygun bir {model_type} üretir.

    `bundle=True` ise ilişkili varlıklar (conflict vb.) + deneyim güncellemeleri de üretilir;
    sonuç MutationResult döner (auto=False ise onaysız öneri).
    """
    return await _run(
        model_type,
        "generate_for_story",
        prompt,
        context=context,
        collection=collection,
        bundle=bundle,
        auto=auto,
        story_id=story_id,
    )


async def edit(
    model_type: str,
    prompt: str,
    *,
    partial_data: dict[str, Any],
    context: str | None = None,
    collection: str | None = None,
) -> BaseModel:
    """Mevcut model verisini (`partial_data`) prompt'a göre düzenler/tamamlar."""
    if partial_data is None:
        raise ValueError("edit() için `partial_data` (dict) zorunludur.")
    return await _run(
        model_type,
        "edit",
        prompt,
        context=context,
        collection=collection,
        partial_data=partial_data,
    )
