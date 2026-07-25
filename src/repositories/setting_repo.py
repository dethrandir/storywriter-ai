from src.clients.database import db


async def serialize(sid: str) -> dict | None:
    return await db.fetchval("SELECT get_setting($1)", sid)


async def resolve_text(sid: str) -> str | None:
    s = await serialize(sid)
    if s is None:
        return None
    lines = [
        f"Setting: {s['name']}",
        f"Style: {s['style']}",
    ]
    if s['time']:
        lines.append(f"Time: {s['time']}")
    if s['location']:
        lines.append(f"Location: {s['location']}")
    if s['environment']:
        lines.append(f"Environment: {s['environment']}")
    if s['environment_details']:
        lines.append(f"Environment Details: {s['environment_details']}")
    if s['social']:
        lines.append(f"Social: {s['social']}")
    if s['mood']:
        lines.append(f"Mood: {s['mood']}")
    if s['sensory_details']:
        lines.append(f"Sensory Details: {s['sensory_details']}")
    if s['info']:
        lines.append(f"Info: {'; '.join(s['info'])}")
    if s['experience']:
        lines.append(f"Experience: {'; '.join(s['experience'])}")
    return "\n".join(lines)
