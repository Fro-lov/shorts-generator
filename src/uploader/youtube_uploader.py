import os
from pathlib import Path
from typing import Optional, List

"""
YouTube Data API v3 Uploader Module

Для работы с официальным YouTube API требуется:
1. Создать проект в Google Cloud Console (https://console.cloud.google.com).
2. Включить 'YouTube Data API v3'.
3. Создать OAuth 2.0 Client ID (Desktop Application) и скачать `client_secrets.json`.
4. Установить библиотеки: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
"""

class YouTubeUploader:
    def __init__(self, client_secrets_file: str = "config/client_secrets.json", token_file: str = "config/youtube_token.pickle"):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file

    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "public"  # 'public', 'private', 'unlisted'
    ):
        """
        Загрузка видеоролика на YouTube Shorts.
        Если видео вертикальное (9:16) и длится менее 3 минут, YouTube автоматически помечает его как #Shorts.
        """
        tags = tags or ["#Shorts", "#Gaming", "#GameDev", "#Bugs"]
        if "#Shorts" not in title and "#Shorts" not in description:
            title = f"{title} #Shorts"

        print(f"[*] Подготовка к загрузке на YouTube: {video_path}")
        print(f"    Заголовок: {title}")
        print(f"    Статус: {privacy_status}")

        # Stub implementation ready to link with google-api-python-client
        print("    [!] Чтобы включить прямую отправку в канал, поместите client_secrets.json в папку config/")
        return {"status": "ready", "video_path": str(video_path), "title": title}
