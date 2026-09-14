import urllib.request
import urllib.parse
import re
from pathlib import Path
from typing import List, Dict, Optional
from config.settings import SFX_DIR


class MyInstantsSFXFetcher:
    """
    Searches and downloads meme sound effects directly from MyInstants.com.
    """
    BASE_URL = "https://www.myinstants.com"

    def __init__(self, target_dir: Path = SFX_DIR):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def search_sound(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        encoded = urllib.parse.quote_plus(query)
        search_url = f"{self.BASE_URL}/en/search/?name={encoded}"
        req = urllib.request.Request(search_url, headers=self.headers)

        results = []
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extract play('/media/sounds/...', ...) and titles
            matches = re.findall(r"play\('(/media/sounds/[^']+)'[^>]*title=\"Play\s+([^\"]+?)\s+sound\"", html)
            for sound_path, title in matches[:limit]:
                results.append({
                    "title": title.strip(),
                    "sound_url": f"{self.BASE_URL}{sound_path}"
                })

            if not results:
                raw_paths = re.findall(r"play\('(/media/sounds/[^']+)'", html)
                for s in raw_paths[:limit]:
                    results.append({
                        "title": query,
                        "sound_url": f"{self.BASE_URL}{s}"
                    })
        except Exception as e:
            print(f"Error searching MyInstants: {e}")

        return results

    def download_sound(self, sound_url: str, filename: Optional[str] = None) -> Path:
        if not filename:
            filename = sound_url.split("/")[-1]
            if not filename.endswith(".mp3"):
                filename += ".mp3"

        out_path = self.target_dir / filename
        req = urllib.request.Request(sound_url, headers=self.headers)

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        with open(out_path, "wb") as f:
            f.write(data)

        print(f"Downloaded SFX: {out_path} ({len(data)} bytes)")
        return out_path

    def get_or_download_sfx(self, query: str, local_filename: str) -> Optional[Path]:
        out_path = self.target_dir / local_filename
        if out_path.exists():
            return out_path

        results = self.search_sound(query, limit=1)
        if results:
            return self.download_sound(results[0]["sound_url"], local_filename)
        return None
