from src.clients.database import db


async def serialize(cid: str) -> dict | None:
    return await db.fetchval("SELECT get_character($1)", cid)


async def resolve_text(cid: str) -> str | None:
    c = await serialize(cid)
    if c is None:
        return None
    lines = [
        f"Character: {c['name']} ({c['full_name']})",
        f"Age: {c['age']}",
        f"Role: {c['role']}",
    ]
    if c['physicality']:
        lines.append(f"Physicality: {c['physicality']}")
    if c['personality']:
        lines.append(f"Personality: {c['personality']}")
    if c['speech_style']:
        lines.append(f"Speech Style: {c['speech_style']}")
    if c['relationships']:
        rels = ", ".join(f"{k}: {v}" for k, v in c['relationships'].items())
        lines.append(f"Relationships: {rels}")
    if c['info']:
        lines.append(f"Info: {'; '.join(c['info'])}")
    if c['experience']:
        lines.append(f"Experience: {'; '.join(c['experience'])}")
    return "\n".join(lines)
