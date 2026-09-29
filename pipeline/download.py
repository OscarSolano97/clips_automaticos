"""Obtiene el video fuente: desde un archivo local o una URL (YouTube, etc.)."""
from __future__ import annotations

import shutil
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


def _download(url: str) -> Path:
    from yt_dlp import YoutubeDL

    settings.work_dir.mkdir(parents=True, exist_ok=True)
    base_opts = {"quiet": True, "no_warnings": True, "skip_download": True}

    with YoutubeDL(base_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    video_id = info.get("id") or "video"

    existing = sorted(settings.work_dir.glob(f"source_{video_id}.*"))
    for ext in (".mp4", ".mkv", ".webm"):
        for f in existing:
            if f.suffix == ext:
                return f
    if existing:
        return existing[0]

    opts = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(settings.work_dir / f"source_{video_id}.%(ext)s"),
        "quiet": True,
        "noprogress": True,
        "ffmpeg_location": ffmpeg_exe(),
    }
    with YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)

    result = settings.work_dir / f"source_{video_id}.mp4"
    if result.exists():
        return result
    matches = sorted(settings.work_dir.glob(f"source_{video_id}.*"))
    if not matches:
        raise RuntimeError(f"No se pudo descargar el video {video_id}")
    return matches[0]
