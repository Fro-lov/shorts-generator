import os
import sys
import io
import json
import time
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


class TikTokUploader:
    """
    Automated TikTok Video Uploader using official TikTok Content Posting API.
    Supports OAuth2 authorization code flow, token caching, chunked video upload, and status polling.
    """

    def __init__(
        self,
        secrets_file: Path = Path("secrets/tiktok/client_secrets.json"),
        token_file: Path = Path("secrets/tiktok/token.json")
    ):
        self.secrets_file = Path(secrets_file)
        self.token_file = Path(token_file)

        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"TikTok secrets file not found: {self.secrets_file}. "
                "Please fill in client_key and client_secret."
            )

        with open(self.secrets_file, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.client_key = self.config.get("client_key")
        self.client_secret = self.config.get("client_secret")
        self.redirect_uri = self.config.get("redirect_uri", "https://local.onter.pp.ua/callback")

    def get_auth_url(self, scopes: str = "video.upload,video.publish", state: str = "gamebug_state") -> str:
        """Generates the TikTok OAuth 2.0 authorization URL."""
        import urllib.parse
        params = {
            "client_key": self.client_key,
            "scope": scopes,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        return f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access_token and refresh_token."""
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        resp = requests.post(url, headers=headers, data=data)
        res_json = resp.json()

        if "access_token" in res_json:
            self._save_token(res_json)
            return res_json
        elif "data" in res_json and "access_token" in res_json["data"]:
            self._save_token(res_json["data"])
            return res_json["data"]
        else:
            raise RuntimeError(f"Failed to get TikTok token: {res_json}")

    def _save_token(self, token_data: Dict[str, Any]):
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        token_data["created_at"] = time.time()
        with open(self.token_file, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
        print("   ✓ TikTok токен сохранен в:", self.token_file)

    def get_access_token(self) -> str:
        """Returns a valid access token, refreshing if needed."""
        if not self.token_file.exists():
            raise FileNotFoundError(
                f"TikTok token file not found: {self.token_file}. "
                f"Please authorize by visiting: {self.get_auth_url()}"
            )

        with open(self.token_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        # Check expiration (TikTok access_token usually valid for 24h = 86400s)
        expires_in = token_data.get("expires_in", 86400)
        created_at = token_data.get("created_at", 0)

        if time.time() - created_at > (expires_in - 300):
            print("[*] Обновление истекшего TikTok токена...")
            return self._refresh_token(token_data.get("refresh_token"))

        return token_data.get("access_token")

    def _refresh_token(self, refresh_token: str) -> str:
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        resp = requests.post(url, headers=headers, data=data)
        res_json = resp.json()
        token_info = res_json.get("data", res_json)

        if "access_token" in token_info:
            self._save_token(token_info)
            return token_info["access_token"]
        raise RuntimeError(f"Failed refreshing TikTok token: {res_json}")

    def get_user_info(self) -> Dict[str, Any]:
        """Fetches basic user info to verify API access without uploading videos."""
        access_token = self.get_access_token()
        url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name,username"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers)
        return resp.json()

    def get_creator_info(self) -> Dict[str, Any]:
        """Queries creator publishing permissions and capabilities."""
        access_token = self.get_access_token()
        url = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        resp = requests.post(url, headers=headers, json={})
        return resp.json()

    def upload_video(
        self,
        video_path: Path,
        title: str,
        tags: Optional[List[str]] = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE"  # "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"
    ) -> Dict[str, Any]:
        """
        Uploads and publishes video directly via TikTok Content Posting API.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        tags = tags or ["#gaming", "#gamedev", "#glitch", "#баги", "#fyp"]
        full_title = f"{title} {' '.join(tags)}".strip()
        file_size = video_path.stat().st_size

        print("=" * 60)
        print("🎵 ЗАГРУЗКА НА TIKTOK (Content Posting API)")
        print("=" * 60)
        print(f"📁 Файл: {video_path.name} ({file_size / (1024*1024):.2f} MB)")
        print(f"🏷  Заголовок: {full_title}")
        print(f"🔒 Доступ: {privacy_level}")

        access_token = self.get_access_token()

        # Step 1: Initialize video post
        init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        payload = {
            "post_info": {
                "title": full_title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }

        print("\n[1/3] Инициализация публикации на сервере TikTok...")
        resp = requests.post(init_url, headers=headers, json=payload)
        res_json = resp.json()

        if resp.status_code != 200 or "data" not in res_json:
            raise RuntimeError(f"TikTok init failed: {res_json}")

        data = res_json["data"]
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")

        # Step 2: Upload Video Binary
        print("\n[2/3] Отправка видеофайла в TikTok...")
        upload_headers = {
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Type": "video/mp4"
        }

        with open(video_path, "rb") as f_vid:
            upload_resp = requests.put(upload_url, headers=upload_headers, data=f_vid)

        if upload_resp.status_code not in (200, 201):
            raise RuntimeError(f"TikTok video chunk upload failed: {upload_resp.status_code} {upload_resp.text}")
        print("   ✓ Файл успешно загружен на CDN TikTok!")

        # Step 3: Poll status
        print("\n[3/3] Ожидание подтверждения обработки TikTok...")
        status_url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
        for attempt in range(12):
            time.sleep(3)
            stat_resp = requests.post(status_url, headers=headers, json={"publish_id": publish_id})
            stat_data = stat_resp.json().get("data", {})
            status = stat_data.get("status")
            print(f"   ✓ Статус: {status}...")

            if status in ("SUCCESS_DIRECT_POST", "PUBLISH_COMPLETE"):
                print("\n✨ [УСПЕХ] ВИДЕО УСПЕШНО ОПУБЛИКОВАНО В TIKTOK!")
                return {"status": "success", "publish_id": publish_id, "title": full_title}
            elif status == "FAILED":
                fail_reason = stat_data.get("fail_reason", "Unknown")
                raise RuntimeError(f"TikTok publishing failed: {fail_reason}")

        print(f"\n✨ Запрос отправлен (ID: {publish_id}). Обработка завершается на стороне TikTok.")
        return {"status": "processing", "publish_id": publish_id, "title": full_title}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TikTok Content Posting API CLI")
    parser.add_argument("video_path", nargs="?", help="Path to video MP4")
    parser.add_argument("--title", type=str, default="Игровой баг", help="Video caption")
    parser.add_argument("--auth-url", action="store_true", help="Print authorization URL")
    parser.add_argument("--code", type=str, help="Exchange auth code from redirect for token")
    parser.add_argument("--check", action="store_true", help="Check token and fetch user & creator info without uploading")
    args = parser.parse_args()

    uploader = TikTokUploader()

    if args.auth_url:
        print("\n👉 Откройте эту ссылку в браузере для авторизации вашего TikTok аккаунта:")
        print(uploader.get_auth_url())
        return

    if args.code:
        uploader.exchange_code_for_token(args.code)
        print("\n[OK] Авторизация успешно выполнена, токен сохранен!")
        return

    if args.check:
        print("\n[*] Проверка профиля пользователя TikTok:")
        user_info = uploader.get_user_info()
        print("User Info Response:", json.dumps(user_info, indent=2, ensure_ascii=False))

        print("\n[*] Проверка разрешений публикации Creator Info:")
        creator_info = uploader.get_creator_info()
        print("Creator Info Response:", json.dumps(creator_info, indent=2, ensure_ascii=False))
        return

    if args.video_path:
        uploader.upload_video(Path(args.video_path), title=args.title)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
