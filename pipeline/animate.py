"""Anima el avatar con image-to-video usando Spaces gratuitos de Hugging Face.

Orden: LTX-Video (movimiento llamativo) -> SVD (micro-movimiento natural) ->
si ambos fallan, se usa el zoom estatico de avatar.build_loop.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import hf
from .config import settings
from .ffmpeg import ffmpeg_exe


def _result_video(result) -> Path:
    if isinstance(result, dict):
        src = result.get("video") or result.get("path")
    else:
        src = result
    if not src:
        raise RuntimeError(f"El Space no devolvio video: {result!r}")
    return Path(src)


def _to_mp4(src: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".mp4":
        shutil.copy2(src, out)
    else:
        subprocess.run(
            [ffmpeg_exe(), "-y", "-i", str(src), "-c:v", "libx264", "-crf", "20",
             "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", str(out)],
            check=True, capture_output=True,
        )
    return out


def _ltx(image: Path, out: Path) -> Path:
    def run() -> Path:
        client = hf.client(settings.avatar_i2v_space)
        result, _seed = client.predict(
            prompt=settings.avatar_motion_prompt,
            negative_prompt=settings.avatar_negative_prompt,
            input_image_filepath=hf.handle(image),
            input_video_filepath=None,
            height_ui=settings.avatar_i2v_height,
            width_ui=settings.avatar_i2v_width,
            mode="image-to-video",
            duration_ui=settings.avatar_i2v_duration,
            ui_frames_to_use=9,
            seed_ui=42,
            randomize_seed=True,
            ui_guidance_scale=1,
            improve_texture_flag=True,
            api_name="/image_to_video",
        )
        return _result_video(result)

    return _to_mp4(hf.call(run), out)


def _svd(image: Path, out: Path) -> Path:
    def run() -> Path:
        client = hf.client(settings.avatar_i2v_fallback)
        result, _seed = client.predict(
            image=hf.handle(image),
            seed=42,
            randomize_seed=True,
            motion_bucket_id=80,
            fps_id=7,
            api_name="/video",
        )
        return _result_video(result)

    return _to_mp4(hf.call(run), out)


def animate_avatar(force: bool = False) -> Path:
    out = settings.assets_dir / "avatar" / "avatar_motion.mp4"
    if out.exists() and not force:
        return out

    image = settings.avatar_image
    if not image.exists():
        raise RuntimeError(
            f"Falta la imagen del avatar ({image}). Corre primero: python cli.py avatar"
        )

    errors: list[str] = []
    for label, fn in (("LTX-Video", _ltx), ("SVD", _svd)):
        try:
            print(f"  Animando con {label}...")
            path = fn(image, out)
            print(f"  Avatar animado con {label}: {path}")
            return path
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {str(exc)[:140]}")

    raise RuntimeError(
        "No se pudo animar el avatar (los Spaces gratis pueden estar ocupados).\n  "
        + "\n  ".join(errors)
        + "\n  -> Se usara el avatar estatico con zoom."
    )
