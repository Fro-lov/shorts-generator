---
name: cdp-motion-shorts
description: Производство вертикальных видеороликов (Shorts/TikTok/Reels) с живым браузерным моушен-дизайном через Chrome DevTools Protocol (CDP), 5-экранными карточками, нативным геймплеем, мемами и аппаратным рендером NVIDIA NVENC.
---

# CDP Motion Shorts Engine: Спецификация и стандарты производства

## 1. Концепция и ключевое отличие движка
Вместо статичных картинок или программной псевдо-отрисовки через Pillow/Canvas, движок использует **прямой захват живого браузерного HTML5/CSS3 рендера через Chrome DevTools Protocol (CDP)**:
* 100% аутентичные CSS-анимации, переходы `0.45s cubic-bezier(0.16, 1, 0.3, 1)`, неоновые свечения (`drop-shadow`, `box-shadow`) и векторная SVG-графика.
* Плавная смена 5 экранов под точные тайминги дикторской речи.
* Никаких артефактов растеризации и наложений.

---

## 2. Вертикальная сетка кадра (1080×1920 Strict Layout)

| Зона кадра | Координаты Y | Назначение |
| :--- | :--- | :--- |
| **Top System Header** | `y=50` | Название игры, тема выпуска и бейдж `LIVE REC` |
| **Gameplay Window** | `y=190`–`y=764` (1000×574 px) | Чистый луп геймплея (`raw_gameplay.mp4`) в неоновой рамке |
| **Pagination Dots** | `y=775` | 5 анимированных точек-индикаторов активного экрана |
| **Dynamic Zone: Memes** | `y=860`–`y=1400` (Фаза 1: 0–14s) | 2 реакционных мема с плавным переходом `fade=0.3s` |
| **Dynamic Zone: Motion Cards** | `y=790`–`y=1380` (1000×590 px) (Фаза 2: 14s..Outro) | 5 живых карточек моушен-дизайна из браузера |
| **Dynamic Zone: Outro** | `y=860` (Фаза 3: Финал) | Анимированная плашка `outro_subscribe_motion.mp4` с родным звуком |
| **Subtitles Zone** | `y=1600`–`y=1700` (`MarginV=260`) | Крупные титры с желтым/бирюзовым хайлайтом ключевых фраз |

---

## 3. Стандарт 5 экранов моушен-дека (5-Screen Modular Motion Deck)

1. **Экран 1 // Такт физики (Параметры и скорость):**
   * Векторный SVG спидометр с анимированным кругом `stroke-dashoffset` и крупной цифрой (76px Mono).
   * Блоки параметров движка (тикрейт PhysX 60 Hz, статус коллизии).
2. **Экран 2 // Графический конвейер (Очереди и буферы):**
   * Анимированный прогресс-бар переполнения очереди (`@keyframes barPulse`).
   * Бейдж ошибки с мягким миганием (`@keyframes blink`).
3. **Экран 3 // Рассинхрон потоков (Сетка сравнения):**
   * Двойная сетка 1:1 (Зеленая плашка `Физика (RAM) // ТВЕРДАЯ` vs Красная плашка `GPU // ПУСТОТА`).
4. **Экран 4 // Момент удара / Событие коллизии:**
   * Крупный шейк-бейдж `СТОЛКНОВЕНИЕ` (`@keyframes shake`) + фактура бага.
5. **Экран 5 // Патч и фикс в коде (IDE Card):**
   * Стилизованное окно редактора с кнопками Mac OS, вкладкой файла (`StreamingManager.cpp`).
   * Подсветка синтаксиса (C++ / C#) с зеленым хайлайтом строки `// FIX!`.

---

## 4. Звуковой стандарт и правила TTS

* **🗣️ 100% Естественный темп (Natural Pacing):**
  * Строжайший запрет на применение фильтров ускорения (`atempo`) или искусственного сжатия таймлайна.
  * Скорость речи: **1.0x** (штатная скорость нейросети ~155 слов/мин).
  * Длительность показа каждой карточки **автоматически привязывается к реальной длительности речевого блока**.
* **Аудио-микс (3 слоя):**
  1. Голос диктора (`ru-RU-SvetlanaNeural` / Piper) — 100% громкость.
  2. Эмбиент `Landing - Godmode.mp3` — громкость `0.15` с фейдами.
  3. Нативная аудиодорожка закрывашки аутро — громкость `0.8` в момент старта блока аутро.

---

## 5. Графические правила и запреты

* 🚫 **ЖЕСТКИЙ ЗАПРЕТ НА ЭМОДЗИ:** Никаких unicode-смайликов (💥, 🚗, ⚡, 💡) на схемах и карточках. Только строгий шрифт, чистая векторная графика и технологичные бейджи.
* 🚫 **ЗАПРЕТ ДВОЙНОГО ОБРАМЛЕНИЯ (No Preview Video Reuse):** В окно геймплея подается только чистый исходник `raw_gameplay.mp4`.
* 🚫 **ЗАПРЕТ НА ПЕРЕКРЫТИЕ КАРТОЧЕК МЕМАМИ:** Мемы выводятся строго в фазе интро (0–14s). Как только стартуют карточки, зона `y=790..1380` на 100% принадлежит моушен-деку.

---

## 6. Базовый код использования движка

```python
import asyncio
from pathlib import Path
from src.core.cdp_motion_engine import CDPMotionEngine

async def build_shorts():
    workdir = Path("output/episode_cdp")
    engine = CDPMotionEngine(workdir=workdir)
    
    # 1. Синтез голоса
    timings, voice_wav, dur = await engine.synthesize_voice_blocks(SCRIPT_BLOCKS)
    
    # 2. Субтитры
    subtitles_ass = engine.generate_subtitles(timings, workdir / "subtitles.ass")
    
    # 3. Запись карточек через CDP
    slide_durations = [b["duration"] for b in timings if b["role"] == "slide"]
    motion_mp4 = await engine.record_motion_deck_cdp(
        html_player_path=Path("assets/templates/motion_cards_player.html"),
        slide_durations=slide_durations,
        output_mp4=workdir / "motion_deck.mp4"
    )
    
    # 4. Финальный монтаж в NVENC
    final_video = engine.assemble_final_video(
        gameplay_path=Path("raw_gameplay.mp4"),
        memes=[Path("meme1.gif"), Path("meme2.gif")],
        motion_deck_path=motion_mp4,
        outro_path=Path("assets/templates/outro_subscribe_motion.mp4"),
        voice_wav_path=voice_wav,
        ambient_music_path=Path("assets/music/ambient/Landing - Godmode.mp3"),
        subtitles_ass_path=subtitles_ass,
        timings=timings,
        output_video_path=workdir / "final_shorts.mp4"
    )
    
    # 5. Smoke Test
    assert engine.smoke_test(final_video), "Video verification failed!"

if __name__ == "__main__":
    asyncio.run(build_shorts())
```
