"""
Tenor Meme & GIF Fetcher for Onter's inn Shorts Engine.
Provides automatic search and downloading of GIF memes, reaction clips, and transparent stickers
from Google Tenor API with a zero-dependency fallback for 100% autonomous operation.
"""

import json
import os
import re
import urllib.parse
import urllib.request
import sys
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR

MEMES_DIR = ASSETS_DIR / "memes"
MEMES_DIR.mkdir(parents=True, exist_ok=True)


class TenorMemeFetcher:
    """
    Searches and downloads GIF memes and transparent stickers via Tenor API (Google)
    or public fallback scraper.
    """

    TENOR_V2_SEARCH_URL = "https://tenor.googleapis.com/v2/search"

    def __init__(self, target_dir: Path = MEMES_DIR, api_key: Optional[str] = None):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        # Check explicit key, env var, or fallback
        self.api_key = api_key or os.getenv("TENOR_API_KEY", "")
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def search_tenor(
        self,
        query: str,
        limit: int = 5,
        search_filter: Optional[str] = None,  # "sticker" for transparent background
    ) -> List[Dict[str, str]]:
        """
        Searches Tenor API (v2 or v1 public key) for matching GIF memes or transparent stickers.
        Returns a list of dicts: [{"title": ..., "gif_url": ..., "mp4_url": ..., "format": ...}]
        """
        results = []

        # 1. Try V2 if API key is supplied
        if self.api_key:
            params = {
                "q": query,
                "client_key": "onters_inn_app",
                "limit": str(limit),
                "media_filter": "gif,tinygif,mp4",
                "key": self.api_key
            }
            if search_filter:
                params["searchfilter"] = search_filter

            url = f"{self.TENOR_V2_SEARCH_URL}?{urllib.parse.urlencode(params)}"
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for item in data.get("results", []):
                    media = item.get("media_formats", {})
                    gif_info = media.get("gif") or media.get("tinygif") or {}
                    mp4_info = media.get("mp4") or media.get("nanomp4") or {}

                    if gif_info.get("url") or mp4_info.get("url"):
                        results.append({
                            "id": item.get("id", ""),
                            "title": item.get("content_description", query),
                            "gif_url": gif_info.get("url") or mp4_info.get("url"),
                            "mp4_url": mp4_info.get("url") or gif_info.get("url"),
                        })
            except Exception as e:
                print(f"[TenorMemeFetcher] Tenor V2 API Notice: {e}")

        # 2. Try Tenor V1 / Giphy Public Keys fallback
        if not results:
            giphy_url = f"https://api.giphy.com/v1/gifs/search?q={urllib.parse.quote(query)}&api_key=dc6zaTOxFJmzC&limit={limit}"
            try:
                req = urllib.request.Request(giphy_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for item in data.get("data", []):
                    images = item.get("images", {})
                    g_url = images.get("original", {}).get("url") or images.get("downsized", {}).get("url")
                    m_url = images.get("original_mp4", {}).get("mp4") or g_url
                    if g_url:
                        results.append({
                            "id": item.get("id", ""),
                            "title": item.get("title", query),
                            "gif_url": g_url,
                            "mp4_url": m_url
                        })
            except Exception as e:
                print(f"[TenorMemeFetcher] Giphy Fallback Notice: {e}")

        # 3. Fallback to DDG search scraper
        if not results:
            results = self._fallback_gif_search(query, limit=limit)

        return results

    def _fallback_gif_search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Scrapes Tenor web search (https://tenor.com/search/...) directly for media.tenor.com URLs.
        Works 100% autonomously without API keys or rate limits.
        """
        slug = re.sub(r"[^\w]+", "-", query.lower()).strip("-")
        tenor_web_url = f"https://tenor.com/search/{slug}-gifs"
        req = urllib.request.Request(tenor_web_url, headers=self.headers)

        results = []
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extract tenor media URLs (gif and mp4)
            matches = re.findall(r"(https://media\.tenor\.com/[^\s\"']+?\.gif)", html)
            seen = set()
            for m_url in matches:
                clean_url = m_url.replace("&amp;", "&")
                if clean_url not in seen:
                    seen.add(clean_url)
                    results.append({
                        "id": str(hash(clean_url)),
                        "title": query,
                        "gif_url": clean_url,
                        "mp4_url": clean_url.replace(".gif", ".mp4")
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[TenorMemeFetcher] Tenor Web Scraper Notice: {e}")

        return results

    def download_meme(
        self, download_url: str, filename: Optional[str] = None
    ) -> Path:
        """
        Downloads the target GIF or MP4 meme to local ASSETS_DIR/memes/.
        """
        if not filename:
            ext = ".mp4" if ".mp4" in download_url.lower() else ".gif"
            safe_name = re.sub(r"[^\w\-]", "_", download_url.split("/")[-1].split("?")[0])
            if not safe_name.endswith(ext):
                safe_name += ext
            filename = safe_name

        out_path = self.target_dir / filename
        req = urllib.request.Request(download_url, headers=self.headers)

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        with open(out_path, "wb") as f:
            f.write(data)

        print(f"[SUCCESS] Downloaded Meme: {out_path} ({len(data)} bytes)")
        return out_path

    def get_or_download_meme(
        self, query: str, local_filename: str, transparent_sticker: bool = False
    ) -> Optional[Path]:
        """
        Helper method: returns local file if present, otherwise searches and downloads.
        """
        out_path = self.target_dir / local_filename
        if out_path.exists():
            return out_path

        s_filter = "sticker" if transparent_sticker else None
        results = self.search_tenor(query, limit=1, search_filter=s_filter)
        if results:
            target_url = results[0]["gif_url"]
            return self.download_meme(target_url, local_filename)

        return None


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    fetcher = TenorMemeFetcher()
    print("[TEST] Searching Tenor for 'hacker typing' meme...")
    res = fetcher.search_tenor("hacker typing", limit=2)
    print(f"Results found: {json.dumps(res, indent=2, ensure_ascii=False)}")
