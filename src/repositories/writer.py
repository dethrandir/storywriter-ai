# writer.py
"""
Entity'ler için generic yazma katmanı. `db_init` şemasındaki tablolarla çalışır.

- create:            yeni kayıt ekler (character için uuid'li özel durum dahil)
- update:            mevcut kaydın verilen alanlarını günceller
- append_experience: `experience` jsonb listesine eleman ekler
- append_to_array:   herhangi bir jsonb liste alanına eleman ekler (linkleme)
"""
import json
from dataclasses import dataclass, field
from enum import Enum

from src.clients.database import db


@dataclass
class EntitySchema:
    table: str
    columns: dict[str, str]  # model alanı -> sütun adı
    json_fields: set[str] = field(default_factory=set)
    public_id_column: str = "id"  # create/update WHERE bu sütuna göre yapılır
    auto_id: bool = False  # True: tablo id'si otomatik (integer), public id başka sütunda


ENTITY_SCHEMAS: dict[str, EntitySchema] = {
    "character": EntitySchema(
        table="characters",
        columns={
            "id": "uuid",
            "story_id": "story_id",
            "name": "name",
            "full_name": "full_name",
            "age": "age",
            "role": "role",
            "physicality": "physicality",
            "personality": "personality",
            "speech_style": "speech_style",
            "relationships": "relationships",
            "info": "info",
            "experience": "experience",
        },
        json_fields={"relationships", "info", "experience"},
        public_id_column="uuid",
        auto_id=True,
    ),
    "setting": EntitySchema(
        table="settings",
        columns={
            "id": "id",
            "story_id": "story_id",
            "name": "name",
            "style": "style",
            "time": "time",
            "location": "location",
            "environment": "environment",
            "environment_details": "environment_details",
            "social": "social",
            "mood": "mood",
            "sensory_details": "sensory_details",
            "info": "info",
            "experience": "experience",
        },
        json_fields={"info", "experience"},
    ),
    "story_metadata": EntitySchema(
        table="story_metadata",
        columns={
            "id": "id",
            "name": "name",
            "authors": "authors",
            "theme": "theme",
            "style_and_tone": "style_and_tone",
            "atmosphere": "atmosphere",
            "summary": "summary",
        },
        json_fields={"authors"},
    ),
    "world": EntitySchema(
        table="worlds",
        columns={
            "id": "id",
            "name": "name",
            "style": "style",
            "summary": "summary",
            "lores": "lores",
            "experience": "experience",
        },
        json_fields={"lores", "experience"},
    ),
    "story": EntitySchema(
        table="stories",
        columns={
            "id": "id",
            "story_metadata": "story_metadata_id",
            "world_id": "world_id",
            "pov": "pov",
            "chapters": "chapters",
        },
        json_fields={"chapters"},
    ),
    "chapter": EntitySchema(
        table="chapters",
        columns={
            "id": "id",
            "title": "title",
            "description": "description",
            "summary": "summary",
            "content": "content",
            "scene_ids": "scene_ids",
        },
        json_fields={"scene_ids"},
    ),
    "scene": EntitySchema(
        table="scenes",
        columns={
            "id": "id",
            "story_id": "story_id",
            "title": "title",
            "setting": "setting",
            "characters": "characters",
            "conflicts": "conflicts",
            "events": "events",
            "summary": "summary",
        },
        json_fields={"characters", "conflicts", "events"},
    ),
    "event": EntitySchema(
        table="events",
        columns={
            "id": "id",
            "story_id": "story_id",
            "title": "title",
            "description": "description",
            "date": "date",
            "summary": "summary",
            "details": "details",
            "characters": "characters",
            "conflicts": "conflicts",
        },
        json_fields={"characters", "conflicts"},
    ),
    "conflict": EntitySchema(
        table="conflicts",
        columns={
            "id": "id",
            "story_id": "story_id",
            "description": "description",
            "effects": "effects",
        },
        json_fields={"effects"},
    ),
    "lore": EntitySchema(
        table="lores",
        columns={
            "id": "id",
            "category": "category",
            "title": "title",
            "content": "content",
        },
        json_fields=set(),
    ),
}


def _schema(entity_type: str) -> EntitySchema:
    schema = ENTITY_SCHEMAS.get(entity_type)
    if schema is None:
        raise ValueError(
            f"Bilinmeyen entity tipi: {entity_type}. "
            f"Seçenekler: {list(ENTITY_SCHEMAS)}"
        )
    return schema


def _row(data: dict[str, object], schema: EntitySchema) -> dict[str, object]:
    """Model alanlarını sütun adlarına çevirir; jsonb alanlarını serialize eder."""
    row: dict[str, object] = {}
    for field_name, column in schema.columns.items():
        if field_name not in data:
            continue
        value = data[field_name]
        if isinstance(value, Enum):
            value = value.value
        if field_name in schema.json_fields and not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        row[column] = value
    return row


async def create(entity_type: str, data: dict[str, object]) -> str:
    """Yeni kayıt oluşturur ve entity'nin public id'sini döndürür."""
    schema = _schema(entity_type)
    row = _row(data, schema)
    if "id" not in row and not schema.auto_id:
        raise ValueError(f"create({entity_type}): 'id' alanı zorunlu.")

    if schema.auto_id:
        # public id uuid sütununda; tablo id'si otomatik üretilir
        columns = [c for c in schema.columns.values() if c != "id"]
    else:
        columns = list(row.keys())

    placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
    column_list = ", ".join(columns)
    query = (
        f"INSERT INTO {schema.table} ({column_list}) "
        f"VALUES ({placeholders}) RETURNING {schema.public_id_column}"
    )
    entity_id = await db.fetchval(query, *[row[c] for c in columns])
    return entity_id or str(data.get("id", ""))


async def update(entity_type: str, entity_id: str, data: dict[str, object]) -> None:
    """Mevcut kaydın verilen alanlarını günceller."""
    schema = _schema(entity_type)
    row = _row(data, schema)
    if not row:
        return

    sets = ", ".join(f"{col} = ${i}" for i, col in enumerate(row, start=1))
    values = list(row.values())
    query = (
        f"UPDATE {schema.table} SET {sets} "
        f"WHERE {schema.public_id_column} = ${len(values) + 1}"
    )
    await db.execute(query, *values, entity_id)


async def append_experience(entity_type: str, entity_id: str, note: str) -> None:
    """`experience` jsonb listesine yeni bir deneyim/not ekler."""
    schema = _schema(entity_type)
    query = (
        f"UPDATE {schema.table} "
        f"SET experience = COALESCE(experience, '[]'::jsonb) || $2::jsonb "
        f"WHERE {schema.public_id_column} = $1"
    )
    await db.execute(query, entity_id, json.dumps([note], ensure_ascii=False))


async def append_to_array(
    entity_type: str, entity_id: str, field: str, value: object
) -> None:
    """Belirtilen jsonb liste alanına eleman ekler (örn. chapter.scene_ids)."""
    schema = _schema(entity_type)
    if field not in schema.json_fields:
        raise ValueError(f"append_to_array: '{field}' jsonb liste alanı değil ({entity_type}).")
    query = (
        f"UPDATE {schema.table} "
        f"SET {field} = COALESCE({field}, '[]'::jsonb) || $2::jsonb "
        f"WHERE {schema.public_id_column} = $1"
    )
    await db.execute(query, entity_id, json.dumps([value], ensure_ascii=False))
