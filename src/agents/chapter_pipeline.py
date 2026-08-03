# chapter_pipeline.py
"""
Bölüm yazma pipeline'ı.

Aşamalar (her biri ayrı çalıştırılabilir/resume edilebilir):
1. plan_chapter            → ChapterPlan (DB'de saklanır; auto=False ise 'planned' = onay bekliyor)
2. draft_scene_summaries   → her ScenePlan için kısa durum anlatısı + Scene entity'si
3. draft_chapter_content   → sahne özetleri + anlatım → bölüm metni (düz yazı)
4. summarize_chapter       → başlık, açıklama, özet
5. finalize_chapter        → Chapter entity oluştur + story.chapters'a bağla
6. revise_chapter          → hedefli düzenleme ("şu paragrafı şöyle yap")

Sahneler chapter'dan bağımsızdır: bölüm oluşturulurken kullanılacak mevcut sahneler
`scenes` parametresiyle iletilir; AI planlarken yeni sahne planları da ekleyebilir.

`auto` deseni: auto=True ise kalıcı değişiklikler (entity create/update) uygulanır;
auto=False ise öneri olarak döndürülür. Plan artefaktları (content, summary, scenes)
her zaman DB'ye yazılır (pipeline resumable).
"""
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic_ai import Agent

from src.clients.ai import get_model
from src.models.chapter_metadata import ChapterMeta
from src.models.chapter_plan import ChapterPlan
from src.models.scene_plan import ScenePlan
from src.propagation import ModelOp, MutationResult, execute
from src.repositories import chapter_plan_repo, chapter_repo, scene_repo, story_repo
from src.repositories import writer
from src.utils.text import clean_model, clean_output

# =============================================================================
# AGENT'LAR
# =============================================================================

PLAN_SYSTEM_PROMPT = """
Sen bir worldbuilding ve hikaye tasarımı asistanısın. Bir hikaye için bölüm (chapter) planı hazırlıyorsun.

Kurallar:
- Çıktı her zaman ChapterPlan şemasına uygun olmalı.
- `id` ve `story_id` değerleri istekte verilir; aynen kullan.
- Kullanıcı tarafından iletilen mevcut sahneler plana `scenes` içinde aynen dahil edilmeli (id'leri korunur).
- Gerekirse yeni sahne planları da ekleyebilirsin (id'leri yeni UUID olur).
- Bir bölüm illaki sahnelerden oluşmak zorunda değil; sahne dışı anlatım kısımlarını `narration` listesinde ver.
- `beats`: sahnenin içindeki olay sırası (story beats). `purpose`: sahnenin bölüme katkısı.
- Türkçe, doğal ve hikayeyle tutarlı ol. Markdown/formatlama ekleme.
"""

SCENE_SUMMARY_SYSTEM_PROMPT = """
Sen bir hikaye tasarımı asistanısın. Bir sahnenin kısa durum anlatısını (summary) yazıyorsun.

Kurallar:
- Uzun prose/roman metni yazma. Birkaç paragraflık kısa bir özet/durum anlatısı yeterli.
- Sahnenin ne olduğunu, ne yaşandığını, kimlerin olduğunu özetle; chapter yazarının bu özetten
  akıcı bir kitap metni kurgulayabilmesi için yeterli içerik ver.
- Türkçe ol. Markdown/formatlama ekleme.
"""

ASSEMBLE_SYSTEM_PROMPT = """
Sen bir roman yazarısın. Verilen sahne özetlerinden ve anlatım notlarından bölümün kitap metnini (düz yazı) yazıyorsun.

Kurallar:
- Sahneleri akıcı bir anlatıda birleştir; gerekiyorsa geçiş cümleleri ekle.
- Verilen tüm öğeleri (karakterler, çatışmalar, olaylar, mekanlar) kullan; çelişki yaratma.
- Yalnızca bölüm metnini döndür. Başlık, özet vb. ekleme.
- Türkçe, edebi ve tutarlı ol.
"""

SUMMARIZE_SYSTEM_PROMPT = """
Sen bir hikaye tasarımı asistanısın. Yazılmış bir bölüm için başlık, kısa açıklama ve özet üretiyorsun.

Kurallar:
- `title`: çarpıcı ve kısa bölüm başlığı.
- `description`: bölümün ne hakkında olduğunu anlatan kısa açıklama (UI için).
- `summary`: bölümün özeti; sonraki bölümlerin yazımında ve embedding'lerde kullanılır.
- Türkçe ol. Markdown/formatlama ekleme.
"""

REVISE_SYSTEM_PROMPT = """
Sen bir editörsün. Yazılmış bir bölüm metninde hedefli düzenlemeler yapıyorsun.

Kurallar:
- Yalnızca kullanıcının talimatına uygun değişikliği yap; değiştirilmeyen kısımları birebir aynen koru.
- Hedef (target) verilmişse yalnızca o kısımı düzenle.
- Çıktı, düzenlenmiş tam bölüm metni olmalı (başlık/not ekleme).
- Türkçe ol.
"""

_agents: dict[str, Agent] = {}


def _agent(name: str, output_type: type, system_prompt: str) -> Agent:
    if name not in _agents:
        _agents[name] = Agent(
            model=get_model(),
            system_prompt=system_prompt,
            output_type=output_type,
        )
    return _agents[name]


# =============================================================================
# YARDIMCILAR
# =============================================================================

async def _story_context(story_id: str) -> str:
    text = await story_repo.resolve_text(story_id)
    return text or ""


async def _rag_context(prompt: str, collection: str | None) -> str:
    if collection is None:
        return ""
    from src.clients.embeddings import get_context

    return await get_context(prompt, collection)


def _persist_scenes(plan: ChapterPlan) -> list[dict[str, Any]]:
    return [sc.model_dump(mode="json") for sc in plan.scenes]


# =============================================================================
# 1. PLAN
# =============================================================================

async def plan_chapter(
    story_id: str,
    prompt: str,
    *,
    scenes: list[str] | None = None,
    context: str | None = None,
    collection: str | None = None,
    auto: bool = True,
) -> ChapterPlan:
    """Bölüm planı üretir ve DB'ye kaydeder. auto=True ise 'approved' başlar."""
    plan_id = str(uuid4())

    story_text = await _story_context(story_id)
    rag = await _rag_context(prompt, collection)
    parts = [f"Hikaye bağlamı:\n{story_text}", rag, context]
    ctx = "\n\n---\n\n".join(filter(None, parts))

    provided: list[dict[str, Any]] = []
    for sid in scenes or []:
        s = await scene_repo.serialize(sid)
        if s:
            provided.append(s)
    provided_text = "\n".join(
        f"- {p['id']}: {p.get('title', '')} — {str(p.get('summary', ''))[:200]}"
        for p in provided
    ) or "yok"

    user_prompt = (
        f"Kullanıcı isteği: {prompt}\n\n"
        f"Kullanılacak mevcut sahneler:\n{provided_text}\n\n"
        f"Planın `id` değeri: {plan_id}\n"
        f"Planın `story_id` değeri: {story_id}\n"
        f"Sahne planlarında mevcut sahnelerin id'leri korunmalı: {[p['id'] for p in provided]}\n"
    )

    result = await _agent("plan", ChapterPlan, PLAN_SYSTEM_PROMPT).run(
        user_prompt + "\n\n" + ctx
    )
    plan: ChapterPlan = clean_model(result.data)
    plan.id = plan_id
    plan.story_id = story_id

    story = await story_repo.serialize(story_id)
    plan.index = len(story.get("chapters", []) or []) + 1 if story else 1

    # İletilen sahnelerin plana dahil olduğunu garanti et
    provided_ids = {p["id"] for p in provided}
    plan_ids = {sc.id for sc in plan.scenes}
    for p in provided:
        if p["id"] not in plan_ids:
            plan.scenes.append(
                ScenePlan(
                    id=p["id"],
                    title=p.get("title", ""),
                    setting=p.get("setting", ""),
                    characters=p.get("characters", []),
                    conflicts=p.get("conflicts", []),
                    events=p.get("events", []),
                    summary=p.get("summary", ""),
                    scene_exists=True,
                )
            )
    for sc in plan.scenes:
        sc.scene_exists = sc.id in provided_ids

    plan.status = "approved" if auto else "planned"
    await chapter_plan_repo.create(plan)
    return plan


async def approve_plan(plan_id: str) -> ChapterPlan | None:
    """Onay bekleyen planı 'approved' yapar."""
    await chapter_plan_repo.update(plan_id, {"status": "approved"})
    return await chapter_plan_repo.get(plan_id)


# =============================================================================
# 2. SAHNE ÖZETLERİ
# =============================================================================

async def draft_scene_summaries(
    plan_id: str,
    *,
    scene_index: int | None = None,
    force: bool = False,
    auto: bool = True,
) -> MutationResult:
    """Her ScenePlan için kısa durum anlatısı üretir; Scene entity'lerini yaratır/günceller."""
    plan = await chapter_plan_repo.get(plan_id)
    if plan is None:
        raise ValueError(f"Plan bulunamadı: {plan_id}")

    story_text = await _story_context(plan.story_id)
    ops: list[ModelOp] = []
    targets = [plan.scenes[scene_index]] if scene_index is not None else plan.scenes

    for sc in targets:
        if not force and sc.scene_exists and sc.summary:
            continue  # mevcut sahnenin özeti zaten var

        beats = "\n".join(f"- {b}" for b in sc.beats) or "—"
        user_prompt = (
            f"Bölüm amacı: {plan.goal or 'belirtilmedi'}\n"
            f"Sahne: {sc.title}\n"
            f"Purpose: {sc.purpose or 'belirtilmedi'}\n"
            f"Setting: {sc.setting or 'belirtilmedi'}\n"
            f"Beat'ler:\n{beats}\n\n"
            f"Bu sahnenin kısa durum anlatısını yaz."
        )
        summary = clean_output(
            (await _agent("scene_summary", str, SCENE_SUMMARY_SYSTEM_PROMPT).run(
                user_prompt + "\n\nHikaye bağlamı:\n" + story_text
            )).data
        )
        sc.summary = summary
        sc.status = "drafted"

        if sc.scene_exists:
            ops.append(
                ModelOp(
                    kind="update",
                    entity_type="scene",
                    entity_id=sc.id,
                    data={"summary": summary},
                    note=f"Sahne özeti güncellendi: {sc.title}",
                )
            )
        else:
            ops.append(
                ModelOp(
                    kind="create",
                    entity_type="scene",
                    data={
                        "id": sc.id,
                        "story_id": plan.story_id,
                        "title": sc.title,
                        "setting": sc.setting,
                        "characters": sc.characters,
                        "conflicts": sc.conflicts,
                        "events": sc.events,
                        "summary": summary,
                    },
                    note=f"Sahne oluşturuldu: {sc.title}",
                )
            )

    await chapter_plan_repo.update(plan_id, {"scenes": _persist_scenes(plan)})
    return await execute(ops, auto)


# =============================================================================
# 3. BÖLÜM METNİ
# =============================================================================

async def draft_chapter_content(
    plan_id: str,
    *,
    context: str | None = None,
    collection: str | None = None,
    auto: bool = True,
) -> ChapterPlan:
    """Sahne özetleri + anlatım → bölümün düz yazı metni."""
    plan = await chapter_plan_repo.get(plan_id)
    if plan is None:
        raise ValueError(f"Plan bulunamadı: {plan_id}")

    scene_texts: list[str] = []
    for sc in plan.scenes:
        summary = sc.summary
        if not summary and sc.scene_exists:
            sdata = await scene_repo.serialize(sc.id)
            summary = (sdata or {}).get("summary", "")
        if summary:
            scene_texts.append(f"SAHNE [{sc.title}]:\n{summary}")

    narration = "\n\n".join(plan.narration) if plan.narration else "yok"
    scene_block = "\n\n".join(scene_texts) or "yok"
    story_text = await _story_context(plan.story_id)
    rag = await _rag_context(plan.goal or plan.title or "", collection)

    user_prompt = (
        f"Bölüm amacı: {plan.goal or 'belirtilmedi'}\n\n"
        f"Sahne özetleri:\n{scene_block}\n\n"
        f"Sahne dışı anlatım notları:\n{narration}\n\n"
        f"Bu bölümün kitap metnini (düz yazı) yaz."
    )
    content = clean_output(
        (await _agent("assemble", str, ASSEMBLE_SYSTEM_PROMPT).run(
            user_prompt + "\n\n---\n\n" + "\n\n".join(filter(None, [story_text, rag, context]))
        )).data
    )
    plan.content = content
    plan.status = "drafting"
    await chapter_plan_repo.update(
        plan_id,
        {"content": content, "status": "drafting"},
    )
    return plan


# =============================================================================
# 4. ÖZETLE
# =============================================================================

async def summarize_chapter(plan_id: str, *, auto: bool = True) -> ChapterPlan:
    """Bölüm için başlık, açıklama ve özet üretir."""
    plan = await chapter_plan_repo.get(plan_id)
    if plan is None:
        raise ValueError(f"Plan bulunamadı: {plan_id}")

    user_prompt = (
        f"Bölüm metni:\n{plan.content[:6000]}\n"
        f"{'…[devamı]' if len(plan.content) > 6000 else ''}\n\n"
        f"Başlık, kısa açıklama ve özet üret."
    )
    meta: ChapterMeta = clean_model(
        (await _agent("summarize", ChapterMeta, SUMMARIZE_SYSTEM_PROMPT).run(user_prompt)).data
    )
    plan.title = meta.title or plan.title
    plan.description = meta.description
    plan.summary = meta.summary
    await chapter_plan_repo.update(
        plan_id,
        {"title": plan.title, "description": plan.description, "summary": plan.summary},
    )
    return plan


# =============================================================================
# 5. FİNALİZE
# =============================================================================

async def finalize_chapter(plan_id: str, *, auto: bool = True) -> MutationResult:
    """Plandan Chapter entity oluşturur ve story.chapters'a bağlar."""
    plan = await chapter_plan_repo.get(plan_id)
    if plan is None:
        raise ValueError(f"Plan bulunamadı: {plan_id}")

    chapter_id = str(uuid4())
    scene_ids = [sc.id for sc in plan.scenes if sc.scene_exists]

    ops = [
        ModelOp(
            kind="create",
            entity_type="chapter",
            data={
                "id": chapter_id,
                "title": plan.title,
                "description": plan.description,
                "summary": plan.summary,
                "content": plan.content,
                "scene_ids": scene_ids,
            },
            note="Bölüm oluşturuldu",
        ),
        ModelOp(
            kind="append_to_array",
            entity_type="story",
            entity_id=plan.story_id,
            field="chapters",
            data={"value": chapter_id},
            note="Bölüm hikayeye bağlandı",
        ),
    ]
    result = await execute(ops, auto)
    if auto:
        await chapter_plan_repo.update(plan_id, {"status": "done"})
    return result


# =============================================================================
# 6. HEDEFLİ REVİZYON
# =============================================================================

async def _revise_text(content: str, instruction: str, target: str | None) -> str:
    user_prompt = f"Bölüm metni:\n{content}\n\n"
    if target:
        user_prompt += f"Hedeflenen kısım: {target}\n"
    user_prompt += f"Talimat: {instruction}\n\nDüzenlenmiş tam metni döndür."
    return clean_output(
        (await _agent("revise", str, REVISE_SYSTEM_PROMPT).run(user_prompt)).data
    )


async def revise_chapter(
    chapter_id: str,
    instruction: str,
    *,
    target: str | None = None,
    auto: bool = True,
) -> str:
    """Finalize edilmiş bölümün hedefli düzenlemesi.

    `target`: değiştirilecek kısmın tam metni veya açıklaması (opsiyonel).
    auto=False ise önerilen metni döndürür, DB'ye yazmaz.
    """
    data = await chapter_repo.serialize(chapter_id)
    if data is None:
        raise ValueError(f"Bölüm bulunamadı: {chapter_id}")

    revised = await _revise_text(data.get("content", ""), instruction, target)
    if auto:
        await writer.update("chapter", chapter_id, {"content": revised})
    return revised


async def revise_plan_content(
    plan_id: str,
    instruction: str,
    *,
    target: str | None = None,
    auto: bool = True,
) -> str:
    """Finalize öncesi plan taslağının hedefli düzenlemesi."""
    plan = await chapter_plan_repo.get(plan_id)
    if plan is None:
        raise ValueError(f"Plan bulunamadı: {plan_id}")

    revised = await _revise_text(plan.content, instruction, target)
    if auto:
        await chapter_plan_repo.update(plan_id, {"content": revised})
    return revised
