# propagation.py
"""
Bölüm sonrası yansıtma (propagation).

Finalize edilmiş bir bölüm analiz edilir; bölümden kaynaklanan:
- yeni varlıklar (event, conflict, lore vb.)
- karakter/setting/world deneyim güncellemeleri
- bağlantılar (event.characters, scene.events vb.)
önerilir ve `auto` moduna göre uygulanır.
"""
from pydantic_ai import Agent

from src.clients.ai import get_model
from src.propagation import PropagationPlan, MutationResult, execute, plan_to_ops
from src.propagation.context import build_propagation_context
from src.repositories import chapter_repo, story_repo
from src.utils.text import clean_model

SYSTEM_PROMPT = """
Sen bir hikaye süreklilik (continuity) editörüsün. Yeni yazılmış bir bölümü analiz edip,
hikaye bağlamıyla tutarlı olacak şekilde nelerin güncellenmesi/oluşturulması gerektiğini öneriyorsun.

Kurallar:
- Çıktı PropagationPlan şemasına uygun olmalı.
- `related_creates`: bölümde ortaya çıkan kalıcı varlıklar (örn. yeni olaylar, çatışmalar, lore parçaları).
  Zaten var olan bir şeyi yeniden oluşturma.
- `experience_updates`: bölümde değişen karakter/setting/world deneyimleri.
  `entity_id` değerleri bağlamdaki varlık dizininden (id'ler) alınmalı; bilinmeyen id kullanma.
- `links`: varlıklar arası bağlantılar (örn. event → characters, scene → events, conflict → effects).
- Yalnızca mantıklı ve bağlamla çelişmeyen önerilerde bulun. Türkçe yaz.
"""

_agent: Agent | None = None


def _propagate_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent(model=get_model(), system_prompt=SYSTEM_PROMPT, output_type=PropagationPlan)
    return _agent


async def _reindex(
    story_id: str, chapter_id: str, scene_ids: list[str], result: MutationResult
) -> None:
    try:
        from src.clients.embeddings import index

        collection = f"story_{story_id}"
        await index("chapter", chapter_id, collection)
        for sid in scene_ids:
            await index("scene", sid, collection)
        result.notes.append("Embedding index güncellendi")
    except Exception as exc:  # Qdrant/Voyage yoksa akışı bozma
        result.notes.append(f"Reindex atlandı: {exc}")


async def propagate_chapter(chapter_id: str, *, auto: bool = True) -> MutationResult:
    """Finalize edilmiş bölümü analiz eder; ilişkili değişiklikleri uygular (auto=True)."""
    chapter = await chapter_repo.serialize(chapter_id)
    if chapter is None:
        raise ValueError(f"Bölüm bulunamadı: {chapter_id}")

    story = await story_repo.find_by_chapter(chapter_id)
    if story is None:
        raise ValueError(f"Bölüm hangi hikayeye ait bulunamadı: {chapter_id}")
    story_id = story["id"]

    context = await build_propagation_context(story_id, chapter_id)
    prompt = (
        f"Yeni bölüm özeti: {chapter.get('summary', '')}\n\n"
        f"Bölüm metni:\n{chapter.get('content', '')[:6000]}\n\n"
        f"---\n\n{context}\n\n"
        f"Bu bölümden kaynaklanan yeni varlıkları, deneyim güncellemelerini ve bağlantıları öner."
    )
    plan: PropagationPlan = clean_model((await _propagate_agent().run(prompt)).data)

    ops, notes = plan_to_ops(story_id, plan)
    result = await execute(ops, auto)
    result.notes.extend(notes)

    if auto:
        await _reindex(story_id, chapter_id, chapter.get("scene_ids", []), result)
    return result
