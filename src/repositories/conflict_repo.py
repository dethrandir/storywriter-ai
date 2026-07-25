from src.clients.database import db


async def serialize(cid: str) -> dict | None:
    return await db.fetchval("SELECT get_conflict($1)", cid)


async def resolve_text(cid: str) -> str | None:
    c = await serialize(cid)
    if c is None:
        return None
    lines = [f"Conflict: {c['description']}"]
    if c['effects']:
        lines.append(f"Effects: {'; '.join(c['effects'])}")
    return "\n".join(lines)
