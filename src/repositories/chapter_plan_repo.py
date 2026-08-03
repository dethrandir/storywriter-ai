# chapter_plan_repo.py
"""
ChapterPlan kayıtlarını `chapter_plans` tablosunda saklar/okur.
Plan modelleri düz + scenes jsonb olduğu için serialize doğrudan SELECT ile yapılır.
"""
import json

from src.clients.database import db
from src.models.chapter_plan import ChapterPlan

_COLUMNS = [
    "id",
    "story_id",
    "index",
    "title",
    "goal",
    "settings",
    "characters",
    "conflicts",
    "events",
    "scenes",
    "narration",
    "planned_summary",
    "description",
    "summary",
    "content",
    "status",
]

_JSON_COLUMNS = {
    "settings",
    "characters",
    "conflicts",
    "events",
    "scenes",
    "narration",
}


async def serialize(plan_id: str) -> dict | None:
    query = f"SELECT {', '.join(_COLUMNS)} FROM chapter_plans WHERE id = $1"
    row = await db.fetchrow(query, plan_id)
    if row is None:
        return None
    data = dict(row)
    for col in _JSON_COLUMNS:
        data[col] = json.loads(data[col] or "[]")
    return data


async def get(plan_id: str) -> ChapterPlan | None:
    data = await serialize(plan_id)
    if data is None:
        return None
    return ChapterPlan.model_validate(data)


async def create(plan: ChapterPlan) -> ChapterPlan:
    data = plan.model_dump(mode="json")
    values: dict[str, object] = {}
    for col in _COLUMNS:
        value = data[col]
        if col in _JSON_COLUMNS:
            value = json.dumps(value, ensure_ascii=False)
        values[col] = value

    columns = ", ".join(values)
    placeholders = ", ".join(f"${i}" for i in range(1, len(values) + 1))
    query = f"INSERT INTO chapter_plans ({columns}) VALUES ({placeholders})"
    await db.execute(query, *values.values())
    return plan


async def update(plan_id: str, data: dict) -> None:
    allowed = {col: data[col] for col in _COLUMNS if col in data and col != "id"}
    if not allowed:
        return
    for col in allowed:
        if col in _JSON_COLUMNS:
            allowed[col] = json.dumps(allowed[col], ensure_ascii=False)

    sets = ", ".join(f"{col} = ${i}" for i, col in enumerate(allowed, start=1))
    values = list(allowed.values())
    query = f"UPDATE chapter_plans SET {sets} WHERE id = ${len(values) + 1}"
    await db.execute(query, *values, plan_id)
