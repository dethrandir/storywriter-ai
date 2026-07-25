import asyncio

from src.clients.database import db
from src.repositories import scene_repo


async def serialize(cid: str) -> dict | None:
    return await db.fetchval("SELECT get_chapter($1)", cid)


async def resolve_text(cid: str) -> str | None:
    c = await serialize(cid)
    if c is None:
        return None
    lines = [f"Chapter: {c['title']}"]
    if c['description']:
        lines.append(f"Description: {c['description']}")
    if c['summary']:
        lines.append(f"Summary: {c['summary']}")
    if c['scene_ids']:
        scene_texts = await asyncio.gather(*[scene_repo.resolve_text(sid) for sid in c['scene_ids']])
        for t in scene_texts:
            if t:
                lines.append(f"\n{t}")
    return "\n".join(lines)
