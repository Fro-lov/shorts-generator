import json
from pathlib import Path
from typing import Dict, Any, List


class MetadataGenerator:
    """
    Generates YouTube Shorts / TikTok / Reels metadata, descriptions, tags, and pinned comments.
    Saves metadata.json and description.txt alongside video.mp4.
    """

    @staticmethod
    def generate(
        scenario_data: Dict[str, Any],
        output_dir: Path,
        duration: float = 38.0
    ) -> Dict[str, Any]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        episode_id = str(scenario_data.get("episode_id", "1"))
        game = scenario_data.get("game", "Видеоигра")
        bug_title = scenario_data.get("bug_title", "Забавный баг")
        custom_meta = scenario_data.get("metadata", {})

        # 1. Title
        clean_game_tag = "".join(c for c in game if c.isalnum())
        title = custom_meta.get(
            "title",
            f"{game}: {bug_title} 💥 (Физика игр)"
        )
        short_title = custom_meta.get(
            "short_title",
            f"{game} — {bug_title} #shorts #игры"
        )

        # 2. Tags
        default_tags = [
            clean_game_tag.lower(),
            game.lower(),
            "shorts",
            "игры",
            "баги",
            "баги в играх",
            "геймдев",
            "игровые приколы",
            "физика в играх",
            "юмор",
            "мемы",
            "видеоигры",
            "gaming",
            "gamedev"
        ]
        tags = custom_meta.get("tags", default_tags)
        hashtags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags[:10]])

        # 3. Description text
        blocks_text = [b.get("text", "") for b in scenario_data.get("blocks", [])]
        hook_text = blocks_text[0] if blocks_text else ""
        
        description = custom_meta.get("description")
        if not description:
            description = (
                f"{hook_text}\n\n"
                f"🎮 Игра: {game}\n"
                f"💥 Баг: {bug_title}\n\n"
                f"Разбираем, как устроен движок и почему физика в играх иногда творит безумие!\n"
                f"Подписывайся на канал, чтобы не пропустить новые разборы багов! 👾\n\n"
                f"{hashtags_str}"
            )

        # 4. Pinned Comment
        pinned_comment = custom_meta.get(
            "pinned_comment",
            f"👇 А с какими самыми нелепыми багами или смертями в {game} сталкивались вы? Пишите в комментариях!"
        )

        metadata = {
            "episode_id": episode_id,
            "game": game,
            "bug_title": bug_title,
            "duration_sec": round(duration, 2),
            "title": title,
            "short_title": short_title,
            "description": description,
            "tags": tags,
            "pinned_comment": pinned_comment,
            "category_id": "20"  # Gaming category on YouTube
        }

        # Save metadata.json
        meta_json_path = output_dir / "metadata.json"
        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Save description.txt (Human friendly, ready to copy-paste)
        desc_txt_path = output_dir / "description.txt"
        desc_content = (
            f"============================================================\n"
            f"📌 ЗАГОЛОВОК ДЛЯ YOUTUBE SHORTS / TIKTOK:\n"
            f"============================================================\n"
            f"{short_title}\n\n"
            f"============================================================\n"
            f"📝 ПОЛНОЕ ОПИСАНИЕ:\n"
            f"============================================================\n"
            f"{description}\n\n"
            f"============================================================\n"
            f"💬 ЗАКРЕПЛЕННЫЙ КОММЕНТАРИЙ (PINNED COMMENT):\n"
            f"============================================================\n"
            f"{pinned_comment}\n\n"
            f"============================================================\n"
            f"🏷 ТЕГИ (TAGS ДЛЯ YOUTUBE STUDIO):\n"
            f"============================================================\n"
            f"{', '.join(tags)}\n"
        )

        with open(desc_txt_path, "w", encoding="utf-8") as f:
            f.write(desc_content)

        return metadata
