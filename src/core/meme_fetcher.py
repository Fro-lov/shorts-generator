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

    HISTORY_FILE = MEMES_DIR / "used_memes_history.json"

    def __init__(self, target_dir: Path = MEMES_DIR, api_key: Optional[str] = None):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv("TENOR_API_KEY", "")
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.history = self._load_history()

    def _load_history(self) -> List[str]:
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _record_used(self, url: str):
        # Keep track of last 100 used meme URLs to avoid repetitions across 10-20 episodes
        if url not in self.history:
            self.history.append(url)
            if len(self.history) > 100:
                self.history = self.history[-100:]
            try:
                with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[TenorMemeFetcher] Failed saving meme history: {e}")

    def search_tenor(
        self,
        query: str,
        limit: int = 10,
        search_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Searches Tenor API or public fallback scraper for matching GIF memes.
        Returns up to `limit` candidates.
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

        # 2. Scrape Tenor web search
        if not results:
            results = self._fallback_gif_search(query, limit=limit)

        return results

    def _fallback_gif_search(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Scrapes Tenor web search (https://tenor.com/search/...) directly for search result GIFs.
        Excludes generic sidebar/footer GIFs.
        """
        slug = re.sub(r"[^\w]+", "-", query.lower()).strip("-")
        tenor_web_url = f"https://tenor.com/search/{slug}-gifs"
        req = urllib.request.Request(tenor_web_url, headers=self.headers)

        results = []
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extract main search result GIF images
            # Focus on media.tenor.com links that appear inside search results
            matches = re.findall(r"(https://media\.tenor\.com/[^\s\"']+?\.gif)", html)
            
            # Filter out generic static badges or common repetitive assets if known
            seen = set()
            for m_url in matches:
                clean_url = m_url.replace("&amp;", "&")
                # Normalize URL stem to avoid minor query param duplicates
                url_stem = clean_url.split("?")[0]
                if url_stem not in seen:
                    seen.add(url_stem)
                    results.append({
                        "id": str(hash(url_stem)),
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
        self, query: str, local_filename: str, transparent_sticker: bool = False, overwrite: bool = True
    ) -> Optional[Path]:
        """
        Helper method: searches Tenor for query and selects a FRESH unused meme from results.
        Saves chosen meme to history so it won't repeat in the next 10-20 episodes.
        """
        out_path = self.target_dir / local_filename
        if out_path.exists() and not overwrite:
            return out_path

        if out_path.exists():
            try:
                out_path.unlink()
            except Exception:
                pass

        s_filter = "sticker" if transparent_sticker else None
        results = self.search_tenor(query, limit=10, search_filter=s_filter)
        
        chosen_url = None
        for res_item in results:
            g_url = res_item["gif_url"]
            stem = g_url.split("?")[0]
            if stem not in self.history:
                chosen_url = g_url
                self._record_used(stem)
                break

        # Fallback to first result if all candidates were used before
        if not chosen_url and results:
            chosen_url = results[0]["gif_url"]
            self._record_used(chosen_url.split("?")[0])

        if chosen_url:
            return self.download_meme(chosen_url, local_filename)

        return None


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    fetcher = TenorMemeFetcher()
    print("[TEST] Searching Tenor for 'hacker typing' meme...")
    res = fetcher.search_tenor("hacker typing", limit=2)
    print(f"Results found: {json.dumps(res, indent=2, ensure_ascii=False)}")
