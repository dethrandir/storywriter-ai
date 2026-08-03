# context.py
"""
Propagation için bağlam oluşturma: hikaye metni + story kapsamındaki varlıkların
id-index'i (LLM'in deneyim güncellemeleri/bağlantılar için id referansı verebilmesi için).
"""
from src.clients.database import db
from src.repositories import chapter_repo, story_repo

_ENTITY_META = {
    "character": ("characters", "uuid", "name"),
    "setting": ("settings", "id", "name"),
    "event": ("events", "id", "title"),
    "conflict": ("conflicts", "id", "description"),
    "scene": ("scenes", "id", "title"),
}


async def entity_index(story_id: str) -> str:
    """Story kapsamındaki varlıkların id + kısa etiket listesi."""
    lines: list[str] = []
    for entity_type, (table, id_col, label_col) in _ENTITY_META.items():
        rows = await db.fetch(
            f"SELECT {id_col} AS id, {label_col} AS label "
            f"FROM {table} WHERE story_id = $1",
            story_id,
        )
        lines.append(f"[{entity_type}]")
        for r in rows:
            label = str(r["label"] or "")[:120]
            lines.append(f"- {r['id']}: {label}")
    return "\n".join(lines)


async def build_propagation_context(
    story_id: str, chapter_id: str | None = None
) -> str:
    story_text = await story_repo.resolve_text(story_id) or ""
    index = await entity_index(story_id)
    parts = [f"Hikaye bağlamı:\n{story_text}", f"Varlık dizini (id'ler):\n{index}"]

    if chapter_id:
        ch = await chapter_repo.serialize(chapter_id)
        if ch:
            parts.append(
                f"Yeni bölüm:\nÖzet: {ch.get('summary', '')}\n"
                f"Metin: {ch.get('content', '')[:6000]}"
            )
    return "\n\n---\n\n".join(parts)
