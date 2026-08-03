import asyncio

from src.clients.database import db
from src.repositories import character_repo, conflict_repo, event_repo


async def serialize(sid: str) -> dict | None:
    return await db.fetchval("SELECT get_scene($1)", sid)


async def resolve_text(sid: str) -> str | None:
    s = await serialize(sid)
    if s is None:
        return None
    lines = [f"Scene: {s['title']}"]
    if s['setting']:
        lines.append(f"Setting: {s['setting']}")
    if s['summary']:
        lines.append(f"Summary: {s['summary']}")
    if s['characters']:
        char_texts = await asyncio.gather(*[character_repo.resolve_text(cid) for cid in s['characters']])
        lines.append("Characters:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in char_texts if t))
    if s['conflicts']:
        conflict_texts = await asyncio.gather(*[conflict_repo.resolve_text(cid) for cid in s['conflicts']])
        lines.append("Conflicts:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in conflict_texts if t))
    if s['events']:
        event_texts = await asyncio.gather(*[event_repo.resolve_text(eid) for eid in s['events']])
        lines.append("Events:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in event_texts if t))
    return "\n".join(lines)
