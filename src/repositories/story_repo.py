import asyncio
import json

from src.clients.database import db
from src.repositories import story_metadata_repo, world_repo, chapter_repo


async def serialize(sid: str) -> dict | None:
    return await db.fetchval("SELECT get_story($1)", sid)


async def find_by_chapter(chapter_id: str) -> dict | None:
    """Bu bölümü referanslayan hikayeyi döndürür (chapters jsonb üzerinden)."""
    row = await db.fetchrow(
        "SELECT * FROM stories WHERE chapters::jsonb @> $1",
        json.dumps([chapter_id]),
    )
    return dict(row) if row else None


async def resolve_text(sid: str) -> str | None:
    s = await serialize(sid)
    if s is None:
        return None
    lines = [f"Story: {s['id']}"]
    metadata = await story_metadata_repo.resolve_text(s['story_metadata_id'])
    if metadata:
        lines.append(metadata)
    world = await world_repo.resolve_text(s['world_id'])
    if world:
        lines.append(f"\n{world}")
    if s['pov']:
        lines.append(f"Point of View: {s['pov']}")
    if s['chapters']:
        chapter_texts = await asyncio.gather(*[chapter_repo.resolve_text(cid) for cid in s['chapters']])
        lines.append("Chapters:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in chapter_texts if t))
    return "\n".join(lines)
