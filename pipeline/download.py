"""Obtiene el video fuente: desde un archivo local o una URL (YouTube, etc.)."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from .config import settings
from .ffmpeg import ffmpeg_exe


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def get_source(src: str) -> Path:
    if is_url(src):
        return _download(src)
    path = Path(src)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    settings.work_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.work_dir / f"local_{path.stem}{path.suffix or '.mp4'}"
    if path.resolve() != dest.resolve():
        shutil.copy2(path, dest)
    return dest


def _yt_opts() -> dict:
    """Opts comunes de yt-dlp.

    - nocheckcertificate: necesario detras de un proxy MITM (config YT_SSL_VERIFY).
    - player_client [default, android]: HD (hasta 1080p) con respaldo Android,
      que evita el error 403 cuando no hay runtime JavaScript.
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": not settings.yt_ssl_verify,
        "extractor_args": {"youtube": {"player_client": ["default", "android"]}},
    }


def _download(url: str) -> Path:
    from yt_dlp import YoutubeDL

    settings.work_dir.mkdir(parents=True, exist_ok=True)

    with YoutubeDL({**_yt_opts(), "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    video_id = info.get("id") or "video"

    existing = sorted(
        f
        for f in settings.work_dir.glob(f"source_{video_id}.*")
        if not f.name.endswith(".part")
    )
    for ext in (".mp4", ".mkv", ".webm"):
        for f in existing:
            if f.suffix == ext:
                return f
    if existing:
        return existing[0]

    opts = {
        **_yt_opts(),
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(settings.work_dir / f"source_{video_id}.%(ext)s"),
        "noprogress": True,
        "ffmpeg_location": ffmpeg_exe(),
    }

    last: Exception | None = None
    for attempt in range(3):
        try:
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            break
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < 2:
                for part in settings.work_dir.glob(f"source_{video_id}*.part"):
                    part.unlink(missing_ok=True)
                time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"No se pudo descargar el video {video_id}: {last}")

    result = settings.work_dir / f"source_{video_id}.mp4"
    if result.exists():
        return result
    matches = sorted(
        f
        for f in settings.work_dir.glob(f"source_{video_id}.*")
        if not f.name.endswith(".part")
    )
    if not matches:
        raise RuntimeError(f"No se pudo descargar el video {video_id}")
    return matches[0]
