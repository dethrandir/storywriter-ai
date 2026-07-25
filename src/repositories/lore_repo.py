from src.clients.database import db


async def serialize(lid: str) -> dict | None:
    return await db.fetchval("SELECT get_lore($1)", lid)


async def resolve_text(lid: str) -> str | None:
    l = await serialize(lid)
    if l is None:
        return None
    lines = [f"Lore: {l['title']}"]
    if l['category']:
        lines.append(f"Category: {l['category']}")
    if l['content']:
        lines.append(f"Content: {l['content']}")
    return "\n".join(lines)
