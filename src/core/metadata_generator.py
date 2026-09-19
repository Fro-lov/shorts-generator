import json
from pathlib import Path
from typing import Dict, Any, List


class MetadataGenerator:
    """
    Generates YouTube Shorts / TikTok / Reels metadata, descriptions, tags, and pinned comments.
    Supports both Russian (ru) and English (en) channels.
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

        lang = scenario_data.get("lang", "ru").lower()
        episode_id = str(scenario_data.get("episode_id", "1"))
        game = scenario_data.get("game", "Game")
        bug_title = scenario_data.get("bug_title", "Physics Glitch")
        custom_meta = scenario_data.get("metadata", {})

        clean_game_tag = "".join(c for c in game if c.isalnum())

        # 1. Title
        if lang == "en":
            title = custom_meta.get("title", f"{game}: {bug_title} 💥 (Game Physics)")
            short_title = custom_meta.get("short_title", f"{game} — {bug_title} #shorts #gaming")
            default_tags = [
                clean_game_tag.lower(),
                game.lower(),
                "shorts",
                "gaming",
                "gamedev",
                "glitch",
                "gamephysics",
                "bug",
                "funnygaming",
                "videogames",
                "memes",
                "fyp"
            ]
        else:
            title = custom_meta.get("title", f"{game}: {bug_title} 💥 (Физика игр)")
            short_title = custom_meta.get("short_title", f"{game} — {bug_title} #shorts #игры")
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

        # 2. Tags
        tags = custom_meta.get("tags", default_tags)
        hashtags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags[:10]])

        # 3. Description text
        blocks_text = [b.get("text", "") for b in scenario_data.get("blocks", [])]
        hook_text = blocks_text[0] if blocks_text else ""
        
        description = custom_meta.get("description")
        if not description:
            if lang == "en":
                description = (
                    f"{hook_text}\n\n"
                    f"🎮 Game: {game}\n"
                    f"💥 Glitch: {bug_title}\n\n"
                    f"Breaking down game engine physics and hilarious glitches!\n"
                    f"Subscribe for more gaming physics breakdowns! 👾\n\n"
                    f"{hashtags_str}"
                )
                pinned_comment = custom_meta.get(
                    "pinned_comment",
                    f"👇 What is the craziest physics glitch you've encountered in {game}? Drop a comment below!"
                )
            else:
                description = (
                    f"{hook_text}\n\n"
                    f"🎮 Игра: {game}\n"
                    f"💥 Баг: {bug_title}\n\n"
                    f"Разбираем, как устроен движок и почему физика в играх иногда творит безумие!\n"
                    f"Подписывайся на канал, чтобы не пропустить новые разборы багов! 👾\n\n"
                    f"{hashtags_str}"
                )
                pinned_comment = custom_meta.get(
                    "pinned_comment",
                    f"👇 А с какими самыми нелепыми багами или поломками в {game} сталкивались вы? Пишите в комментариях!"
                )
        else:
            pinned_comment = custom_meta.get("pinned_comment", "👇 Comment below!")

        metadata = {
            "episode_id": episode_id,
            "lang": lang,
            "game": game,
            "bug_title": bug_title,
            "duration_sec": round(duration, 2),
            "title": title,
            "short_title": short_title,
            "description": description,
            "tags": tags,
            "pinned_comment": pinned_comment,
            "category_id": "20"
        }

        # Save metadata.json
        meta_json_path = output_dir / "metadata.json"
        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Save description.txt
        desc_txt_path = output_dir / "description.txt"
        header_title = "TITLE (SHORTS / TIKTOK):" if lang == "en" else "ЗАГОЛОВОК ДЛЯ YOUTUBE SHORTS / TIKTOK:"
        header_desc = "FULL DESCRIPTION:" if lang == "en" else "ПОЛНОЕ ОПИСАНИЕ:"
        header_pin = "PINNED COMMENT:" if lang == "en" else "ЗАКРЕПЛЕННЫЙ КОММЕНТАРИЙ (PINNED COMMENT):"
        header_tags = "TAGS (YOUTUBE STUDIO):" if lang == "en" else "ТЕГИ (TAGS ДЛЯ YOUTUBE STUDIO):"

        desc_content = (
            f"============================================================\n"
            f"📌 {header_title}\n"
            f"============================================================\n"
            f"{short_title}\n\n"
            f"============================================================\n"
            f"📝 {header_desc}\n"
            f"============================================================\n"
            f"{description}\n\n"
            f"============================================================\n"
            f"💬 {header_pin}\n"
            f"============================================================\n"
            f"{pinned_comment}\n\n"
            f"============================================================\n"
            f"🏷 {header_tags}\n"
            f"============================================================\n"
            f"{', '.join(tags)}\n"
        )

        with open(desc_txt_path, "w", encoding="utf-8") as f:
            f.write(desc_content)

        return metadata
