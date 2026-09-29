"""Helper para obtener el binario de FFmpeg (incluido via imageio-ffmpeg)."""
from __future__ import annotations

import shutil
from functools import lru_cache


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "No se encontro FFmpeg. Instala imageio-ffmpeg (pip install imageio-ffmpeg) "
            "o FFmpeg del sistema."
        ) from exc
