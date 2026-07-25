from src.repositories import (
    character_repo,
    chapter_repo,
    conflict_repo,
    event_repo,
    lore_repo,
    scene_repo,
    setting_repo,
    story_metadata_repo,
    story_repo,
    world_repo,
)

repos = {
    "character": character_repo,
    "chapter": chapter_repo,
    "conflict": conflict_repo,
    "event": event_repo,
    "lore": lore_repo,
    "scene": scene_repo,
    "setting": setting_repo,
    "story_metadata": story_metadata_repo,
    "story": story_repo,
    "world": world_repo,
}