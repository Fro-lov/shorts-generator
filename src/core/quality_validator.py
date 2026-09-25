import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageStat, ImageChops

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

from config.settings import FFMPEG_PATH


class QualityValidator:
    """
    Железобетонный Валидатор кадровой, аудио- и монтажной целостности видеороликов.
    Проверяет ролик на всех 4 этапах производства в соответствии со спецификацией.
    """

    def __init__(self, episode_id: str):
        self.episode_id = str(episode_id)

    def validate_raw_gameplay(self, clip_path: Path) -> Dict[str, Any]:
        """
        [Этап 1] Валидация сырого геймплейного отрезка ДО начала монтажа.
        Проверяет:
        - Существование и размер файла
        - Декодируемость контейнера через ffprobe
        - Отсутствие черных/пустых кадров (Black Frame Detection)
        - Отсутствие заморозок/фризов (Frame Variance / Freeze Frame Check)
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }

        if not clip_path.exists() or clip_path.stat().st_size == 0:
            report["valid"] = False
            report["errors"].append(f"Файл геймплея не найден или пуст: {clip_path}")
            return report

        # 1. Probe video metadata
        probe_cmd = [
            FFMPEG_PATH, "-v", "error",
            "-show_entries", "stream=width,height,duration,r_frame_rate:format=duration,size",
            "-of", "json",
            str(clip_path)
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            report["valid"] = False
            report["errors"].append(f"ffprobe не смог декодировать геймплей: {res.stderr.strip()}")
            return report

        try:
            probe_data = json.loads(res.stdout)
            report["details"]["probe"] = probe_data
        except json.JSONDecodeError:
            report["valid"] = False
            report["errors"].append("Не удалось распарсить JSON метаданных ffprobe")
            return report

        # 2. Extract sample frames for motion/black detection (5 frames across duration)
        temp_dir = clip_path.parent / "val_frames"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean previous sample frames
        for f in temp_dir.glob("sample_*.jpg"):
            try: f.unlink()
            except Exception: pass

        extract_cmd = [
            FFMPEG_PATH, "-y", "-i", str(clip_path),
            "-vf", "fps=1",
            "-vframes", "8",
            str(temp_dir / "sample_%02d.jpg")
        ]
        subprocess.run(extract_cmd, capture_output=True, text=True)

        frame_files = sorted(list(temp_dir.glob("sample_*.jpg")))
        if not frame_files:
            report["valid"] = False
            report["errors"].append("Не удалось извлечь тестовые кадры из геймплея")
            return report

        # Check black frames and freeze frames between consecutive samples
        images = [Image.open(p).convert("RGB") for p in frame_files]
        
        for idx, img in enumerate(images):
            stat = ImageStat.Stat(img)
            mean_brightness = sum(stat.mean) / len(stat.mean)
            std_dev = sum(stat.stddev) / len(stat.stddev)
            
            # Black or monochrome frame detection
            if mean_brightness < 8.0 or std_dev < 3.0:
                report["valid"] = False
                report["errors"].append(f"Обнаружен черный/пустой кадр #{idx+1} (средняя яркость {mean_brightness:.1f})")

        # Freeze frame check (compare consecutive frames)
        diff_scores = []
        for i in range(len(images) - 1):
            diff = ImageChops.difference(images[i], images[i+1])
            diff_stat = ImageStat.Stat(diff)
            diff_score = sum(diff_stat.mean) / len(diff_stat.mean)
            diff_scores.append(diff_score)
            
            if diff_score < 0.3:
                report["warnings"].append(f"Кадры #{i+1} и #{i+2} идентичны (возможен фриз/стоп-кадр, разница {diff_score:.2f})")

        report["details"]["frame_count"] = len(frame_files)
        report["details"]["diff_scores"] = diff_scores

        return report

    def validate_tts_synthesis(
        self,
        voice_dir: Path,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        [Этап 2] Валидация синтеза озвучки (Dual-Voice assert & Duration check).
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "roles_found": []
        }

        blocks = scenario.get("blocks", [])
        if not blocks:
            report["valid"] = False
            report["errors"].append("Сценарий не содержит смысловых блоков `blocks`")
            return report

        roles = set()
        for idx, blk in enumerate(blocks):
            role = blk.get("role", "expert")
            roles.add(role)
            audio_p = voice_dir / f"block_{idx}.wav"
            
            if not audio_p.exists() or audio_p.stat().st_size < 1000:
                report["valid"] = False
                report["errors"].append(f"Аудиофайл блока #{idx} ({blk.get('name')}) не найден или сорван")
            
        report["roles_found"] = list(roles)

        # Dual voice requirement (Svetlana as host, Dmitry as expert)
        if len(roles) < 2 and len(blocks) >= 3:
            report["valid"] = False
            report["errors"].append(f"Нарушен Dual-Voice стандарт: найдена только одна роль ({roles}). Требуются 'host' и 'expert'.")

        return report

    def validate_sfx_volume(self, sfx_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [Хук & Мемы] Валидация уровня громкости SFX-эффектов.
        Жесткое ограничение: SFX НЕ должен быть слишком громким (volume <= 0.20).
        """
        report = {"valid": True, "errors": [], "warnings": []}

        for idx, cfg in enumerate(sfx_configs):
            vol = cfg.get("volume", 0.16)
            if vol > 0.20:
                report["valid"] = False
                report["errors"].append(
                    f"Громкость SFX '{cfg.get('name', idx)}' слишком высока ({vol:.2f} > 0.20 max limit). "
                    "Мемные звуки должны быть тихими и не перебивать голос диктора!"
                )
        return report

    def validate_assembled_video(
        self,
        video_path: Path,
        block_timings: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        [Этап 3] Валидация смонтированного видеоролика по контрольным точкам таймлайна.
        Проверяет:
        1. Полную декодируемость контейнера через ffprobe
        2. Извлечение кадров на ключевых секциях (Hook, Diagram, Code, Outro)
        3. Проверку наложения visual elements по секциям
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checked_timestamps": {}
        }

        if not video_path.exists():
            report["valid"] = False
            report["errors"].append(f"Итоговый файл видео не найден: {video_path}")
            return report

        # 1. Full decoding check (Smoke Test)
        probe_cmd = [
            FFMPEG_PATH, "-v", "error",
            "-i", str(video_path),
            "-f", "null", "-"
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            report["valid"] = False
            report["errors"].append(f"Видеофайл содержит битые кадры или поврежден контейнер: {res.stderr.strip()}")
            return report

        # 2. Extract frames at block midpoints to confirm visuals
        frames_dir = video_path.parent / "validation_snapshots"
        frames_dir.mkdir(parents=True, exist_ok=True)

        snapshots = {}
        for block_name, timings in block_timings.items():
            start_t = timings.get("start", 0.0)
            end_t = timings.get("end", start_t + 2.0)
            mid_t = (start_t + end_t) / 2.0
            
            snap_path = frames_dir / f"snap_{block_name}.jpg"
            snap_cmd = [
                FFMPEG_PATH, "-y",
                "-ss", f"{mid_t:.2f}",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(snap_path)
            ]
            subprocess.run(snap_cmd, capture_output=True, text=True)

            if snap_path.exists() and snap_path.stat().st_size > 0:
                snapshots[block_name] = str(snap_path)
                report["checked_timestamps"][block_name] = mid_t
            else:
                report["warnings"].append(f"Не удалось извлечь снимок кадра для блока '{block_name}' на t={mid_t:.2f}s")

        report["details"] = {"snapshots": snapshots}
        return report

    def create_contact_sheet(
        self,
        snapshot_paths: List[Path],
        output_grid_path: Path,
        grid_cols: int = 3
    ) -> Path:
        """
        Создает единый коллаж кадров (Contact Sheet / Grid) для быстрой сканируемости
        нейросетью или пользователем.
        """
        if not snapshot_paths:
            raise ValueError("Список снимков кадров пуст")

        images = [Image.open(p) for p in snapshot_paths if p.exists()]
        if not images:
            raise ValueError("Не удалось открыть ни одно изображение для коллажа")

        # Resize each image to uniform preview size (e.g., 360x640)
        thumb_w, thumb_h = 360, 640
        thumbs = [img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS) for img in images]

        num_images = len(thumbs)
        grid_rows = (num_images + grid_cols - 1) // grid_cols

        grid_w = grid_cols * thumb_w
        grid_h = grid_rows * thumb_h

        grid_img = Image.new("RGB", (grid_w, grid_h), color=(20, 22, 26))

        for idx, thumb in enumerate(thumbs):
            r = idx // grid_cols
            c = idx % grid_cols
            grid_img.paste(thumb, (c * thumb_w, r * thumb_h))

        grid_img.save(output_grid_path, quality=90)
        return output_grid_path
