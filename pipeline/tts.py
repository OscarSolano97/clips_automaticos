"""Genera la voz del avatar (espanol) con Kokoro, via Space gratuito de HF."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import hf
from .config import settings


def generate(
    text: str,
    out_path: Path,
    voice: str | None = None,
    speed: float | None = None,
) -> Path | None:
    text = (text or "").strip()
    if not text:
        return None

    voice = voice or settings.tts_voice
    speed = speed if speed is not None else settings.tts_speed

    def run() -> str:
        client = hf.client(settings.tts_space)
        result = client.predict(text=text, voice=voice, speed=speed, api_name="/predict")
        src = result.get("path") if isinstance(result, dict) else result
        if not src:
            raise RuntimeError("El Space de TTS no devolvio audio")
        return src

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(hf.call(run), out_path)
    return out_path
