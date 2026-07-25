import asyncio

from src.clients.database import db
from src.repositories import character_repo, conflict_repo


async def serialize(eid: str) -> dict | None:
    return await db.fetchval("SELECT get_event($1)", eid)


async def resolve_text(eid: str) -> str | None:
    e = await serialize(eid)
    if e is None:
        return None
    lines = [f"Event: {e['title']}"]
    if e['description']:
        lines.append(f"Description: {e['description']}")
    if e['date']:
        lines.append(f"Date: {e['date']}")
    if e['summary']:
        lines.append(f"Summary: {e['summary']}")
    if e['details']:
        lines.append(f"Details: {e['details']}")
    if e['characters']:
        char_texts = await asyncio.gather(*[character_repo.resolve_text(cid) for cid in e['characters']])
        lines.append("Characters:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in char_texts if t))
    if e['conflicts']:
        conflict_texts = await asyncio.gather(*[conflict_repo.resolve_text(cid) for cid in e['conflicts']])
        lines.append("Conflicts:\n  " + "\n  ".join(t.replace("\n", "\n  ") for t in conflict_texts if t))
    return "\n".join(lines)
