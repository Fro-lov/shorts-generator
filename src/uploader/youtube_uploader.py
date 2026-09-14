import os
import sys
import io
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]


class YouTubeUploader:
    """
    Automated YouTube Shorts Uploader using official YouTube Data API v3.
    Supports OAuth2 credentials caching, resumable uploads, tags, and category assignment.
    """

    def __init__(
        self,
        secrets_dir: Path = Path("secrets/youtube"),
        token_path: Path = Path("secrets/youtube/token.pickle")
    ):
        self.secrets_dir = Path(secrets_dir)
        self.token_path = Path(token_path)
        self.secrets_file = self._find_client_secrets()

    def _find_client_secrets(self) -> Path:
        """Finds any client_secret*.json file in secrets/youtube or config/."""
        if self.secrets_dir.exists():
            for f in self.secrets_dir.glob("*.json"):
                if "client_secret" in f.name or f.name.endswith(".json"):
                    return f

        config_dir = Path("config")
        for f in config_dir.glob("*.json"):
            if "client_secret" in f.name:
                return f

        raise FileNotFoundError(
            f"Client secrets JSON not found in {self.secrets_dir} or {config_dir}."
        )

    def get_authenticated_service(self):
        """Authenticates user via OAuth2 and caches credentials in token.pickle."""
        credentials = None

        if self.token_path.exists():
            with open(self.token_path, "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("[*] Обновление истекшего OAuth токена...")
                credentials.refresh(Request())
            else:
                print("[*] Первичная авторизация через браузер...")
                print(f"    Используем ключ: {self.secrets_file.name}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.secrets_file),
                    SCOPES
                )
                credentials = flow.run_local_server(
                    port=0,
                    prompt="consent",
                    authorization_prompt_message="Для авторизации перейдите по ссылке: {url}",
                    success_message="Авторизация успешно завершена! Можете закрыть эту вкладку."
                )

            # Save credentials for future automated runs
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "wb") as token:
                pickle.dump(credentials, token)
            print("   ✓ Токен успешно сохранен в:", self.token_path)

        return build("youtube", "v3", credentials=credentials)

    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",  # 'public', 'unlisted', 'private'
        category_id: str = "20"          # 20 = Gaming
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube as a Short.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Ensure Shorts hashtag in title or description
        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        tags = tags or ["Shorts", "Gaming", "GameDev", "Баги", "Gamer"]

        print("=" * 60)
        print("🎬 ЗАГРУЗКА НА YOUTUBE SHORTS")
        print("=" * 60)
        print(f"📁 Файл: {video_path.name} ({video_path.stat().st_size / (1024*1024):.2f} MB)")
        print(f"🏷  Заголовок: {title}")
        print(f"🔒 Доступ: {privacy_status}")

        youtube = self.get_authenticated_service()

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4"
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        print("\n⏳ Отправка видеофайла в YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   ✓ Загружено: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        shorts_url = f"https://youtube.com/shorts/{video_id}"

        print("\n✨ [УСПЕХ] ВИДЕО УСПЕШНО ОПУБЛИКОВАНО НА YOUTUBE!")
        print(f"🔗 Ссылка: {video_url}")
        print(f"📱 Shorts: {shorts_url}")

        return {
            "status": "success",
            "video_id": video_id,
            "url": video_url,
            "shorts_url": shorts_url,
            "title": title
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Upload a video to YouTube Shorts")
    parser.add_argument("video_path", type=str, help="Path to the video MP4 file")
    parser.add_argument("--title", type=str, default="Игровой баг #Shorts", help="Video title")
    parser.add_argument("--description", type=str, default="Разбор бага в видеоигре #Shorts", help="Video description")
    parser.add_argument("--status", type=str, default="public", choices=["public", "unlisted", "private"], help="Privacy status")
    args = parser.parse_args()

    uploader = YouTubeUploader()
    uploader.upload_short(
        video_path=Path(args.video_path),
        title=args.title,
        description=args.description,
        privacy_status=args.status
    )


if __name__ == "__main__":
    main()
