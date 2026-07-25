from src.clients.database import db


async def serialize(mid: str) -> dict | None:
    return await db.fetchval("SELECT get_story_metadata($1)", mid)


async def resolve_text(mid: str) -> str | None:
    m = await serialize(mid)
    if m is None:
        return None
    lines = [
        f"Story: {m['name']}",
        f"Theme: {m['theme']}",
    ]
    if m['authors']:
        lines.append(f"Authors: {', '.join(m['authors'])}")
    if m['style_and_tone']:
        lines.append(f"Style and Tone: {m['style_and_tone']}")
    if m['atmosphere']:
        lines.append(f"Atmosphere: {m['atmosphere']}")
    if m['summary']:
        lines.append(f"Summary: {m['summary']}")
    return "\n".join(lines)
