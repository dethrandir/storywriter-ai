import asyncio

from src.clients.database import db
from src.repositories import lore_repo


async def serialize(wid: str) -> dict | None:
    return await db.fetchval("SELECT get_world($1)", wid)


async def resolve_text(wid: str) -> str | None:
    w = await serialize(wid)
    if w is None:
        return None
    lines = [
        f"World: {w['name']}",
        f"Style: {w['style']}",
    ]
    if w['summary']:
        lines.append(f"Summary: {w['summary']}")
    if w['lores']:
        lore_texts = await asyncio.gather(*[lore_repo.resolve_text(lid) for lid in w['lores']])
        lines.append("Lores:\n  " + "\n  ".join(t for t in lore_texts if t))
    if w['experience']:
        lines.append(f"Experience: {'; '.join(w['experience'])}")
    return "\n".join(lines)
