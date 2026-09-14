import math
import wave
import struct
from pathlib import Path
from config.settings import MUSIC_DIR


def generate_investigation_bgm(output_wav: Path, duration: float = 45.0, sample_rate: int = 44100):
    """
    Synthesizes a royalty-free cinematic dark investigation suspense ambient track.
    Features:
    - Deep sub-bass drone (D minor / A minor)
    - Ticking suspense clockwork pulse (100 BPM)
    - Mysterious dark synth pad swell with harmonic overtones
    - Low volume, perfect for background audio ducking.
    """
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    num_samples = int(duration * sample_rate)
    samples = []

    bpm = 100.0
    beat_interval = 60.0 / bpm

    for i in range(num_samples):
        t = i / sample_rate

        # 1. Dark Sub Drone (D1: 36.7 Hz + D2: 73.4 Hz + subtle detune 36.9 Hz)
        drone = (
            0.35 * math.sin(2 * math.pi * 36.7 * t) +
            0.20 * math.sin(2 * math.pi * 73.4 * t) +
            0.15 * math.sin(2 * math.pi * 36.9 * t)
        )

        # 2. Suspense Swell Pad (Minor 3rd: F2 87.3Hz, 5th: A2 110Hz, with slow LFO 0.2Hz)
        lfo = 0.5 * (1.0 + math.sin(2 * math.pi * 0.25 * t))
        pad = lfo * (
            0.15 * math.sin(2 * math.pi * 87.3 * t) +
            0.12 * math.sin(2 * math.pi * 110.0 * t) +
            0.08 * math.sin(2 * math.pi * 174.6 * t)  # F3
        )

        # 3. Mystery Pulse / Tension click (every beat)
        beat_phase = (t % beat_interval) / beat_interval
        if beat_phase < 0.08:
            pulse_env = math.exp(-beat_phase * 60.0)
            pulse = pulse_env * (0.2 * math.sin(2 * math.pi * 1200 * t) + 0.1 * math.sin(2 * math.pi * 2400 * t))
        else:
            pulse = 0.0

        # Master mix
        mix = (drone + pad + pulse) * 0.65
        # Soft clamp
        mix = max(-0.95, min(0.95, mix))

        # Convert to 16-bit PCM integer
        sample_val = int(mix * 32767.0)
        samples.append(sample_val)

    with wave.open(str(output_wav), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        packed_data = struct.pack(f"<{len(samples)}h", *samples)
        f.writeframes(packed_data)

    print(f"Generated investigation music: {output_wav}")
    return output_wav


import random

def get_random_bgm(music_dir: Path = MUSIC_DIR) -> Path:
    """
    Picks a background music track from assets/music/, ignoring SFX like 'колокольня'.
    """
    candidates = [
        f for f in music_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ('.wav', '.mp3', '.ogg', '.m4a') and 'колокол' not in f.name.lower()
    ]
    if candidates:
        return random.choice(candidates)
    
    # Fallback to generated ambient
    default_bgm = music_dir / "investigation_ambient.wav"
    if not default_bgm.exists():
        generate_investigation_bgm(default_bgm)
    return default_bgm


if __name__ == "__main__":
    generate_investigation_bgm(MUSIC_DIR / "investigation_ambient.wav", duration=45.0)
