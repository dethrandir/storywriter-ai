# db_init.py
from src.clients.database import db

async def init_db():
    await db.connect()
    async with db.transaction() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                uuid TEXT NOT NULL,
                name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                age TEXT NOT NULL,
                role TEXT NOT NULL,
                physicality TEXT NOT NULL,
                personality TEXT NOT NULL,
                speech_style TEXT NOT NULL,
                relationships JSONB NOT NULL DEFAULT '{}',
                info JSONB NOT NULL DEFAULT '[]',
                experience JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                style TEXT NOT NULL DEFAULT '',
                time TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                environment TEXT NOT NULL DEFAULT '',
                environment_details TEXT NOT NULL DEFAULT '',
                social TEXT NOT NULL DEFAULT '',
                mood TEXT NOT NULL DEFAULT '',
                sensory_details TEXT NOT NULL DEFAULT '',
                info JSONB NOT NULL DEFAULT '[]',
                experience JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS story_metadata (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                authors JSONB NOT NULL DEFAULT '[]',
                theme TEXT NOT NULL DEFAULT '',
                style_and_tone TEXT NOT NULL DEFAULT '',
                atmosphere TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT ''
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worlds (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                style TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                lores JSONB NOT NULL DEFAULT '[]',
                experience JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                story_metadata_id TEXT NOT NULL REFERENCES story_metadata(id),
                world_id TEXT NOT NULL REFERENCES worlds(id),
                pov TEXT NOT NULL,
                chapters JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chapters (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                scene_ids JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                setting TEXT NOT NULL DEFAULT '',
                characters JSONB NOT NULL DEFAULT '[]',
                conflicts JSONB NOT NULL DEFAULT '[]',
                events JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '',
                characters JSONB NOT NULL DEFAULT '[]',
                conflicts JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT '',
                effects JSONB NOT NULL DEFAULT '[]'
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lores (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT ''
            );
            """
        )

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_character(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', c.uuid,
                    'name', c.name,
                    'full_name', c.full_name,
                    'age', c.age,
                    'role', c.role,
                    'physicality', c.physicality,
                    'personality', c.personality,
                    'speech_style', c.speech_style,
                    'relationships', c.relationships,
                    'info', c.info,
                    'experience', c.experience
                ) INTO result
                FROM characters c WHERE c.uuid = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_setting(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', s.id,
                    'name', s.name,
                    'style', s.style,
                    'time', s.time,
                    'location', s.location,
                    'environment', s.environment,
                    'environment_details', s.environment_details,
                    'social', s.social,
                    'mood', s.mood,
                    'sensory_details', s.sensory_details,
                    'info', s.info,
                    'experience', s.experience
                ) INTO result
                FROM settings s WHERE s.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_story_metadata(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', m.id,
                    'name', m.name,
                    'authors', m.authors,
                    'theme', m.theme,
                    'style_and_tone', m.style_and_tone,
                    'atmosphere', m.atmosphere,
                    'summary', m.summary
                ) INTO result
                FROM story_metadata m WHERE m.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_world(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', w.id,
                    'name', w.name,
                    'style', w.style,
                    'summary', w.summary,
                    'lores', w.lores,
                    'experience', w.experience
                ) INTO result
                FROM worlds w WHERE w.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_story(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', s.id,
                    'story_metadata_id', s.story_metadata_id,
                    'world_id', s.world_id,
                    'pov', s.pov,
                    'chapters', s.chapters
                ) INTO result
                FROM stories s WHERE s.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_chapter(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', c.id,
                    'title', c.title,
                    'description', c.description,
                    'summary', c.summary,
                    'content', c.content,
                    'scene_ids', c.scene_ids
                ) INTO result
                FROM chapters c WHERE c.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_scene(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', s.id,
                    'title', s.title,
                    'setting', s.setting,
                    'characters', s.characters,
                    'conflicts', s.conflicts,
                    'events', s.events
                ) INTO result
                FROM scenes s WHERE s.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_event(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', e.id,
                    'title', e.title,
                    'description', e.description,
                    'date', e.date,
                    'summary', e.summary,
                    'details', e.details,
                    'characters', e.characters,
                    'conflicts', e.conflicts
                ) INTO result
                FROM events e WHERE e.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_conflict(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', c.id,
                    'description', c.description,
                    'effects', c.effects
                ) INTO result
                FROM conflicts c WHERE c.id = _id;
                RETURN result;
            END;
            $$;
        """)

        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_lore(_id TEXT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', l.id,
                    'category', l.category,
                    'title', l.title,
                    'content', l.content
                ) INTO result
                FROM lores l WHERE l.id = _id;
                RETURN result;
            END;
            $$;
        """)