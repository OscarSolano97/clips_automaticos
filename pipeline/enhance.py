"""Mejora el rostro del avatar con CodeFormer (Space gratuito de Hugging Face)."""
from __future__ import annotations

import shutil
from pathlib import Path

from . import hf
from .config import settings


def _enhance(source: Path) -> Path:
    def run() -> Path:
        client = hf.client(settings.enhance_space)
        result, _msg = client.predict(
            image=hf.handle(source),
            face_align=True,
            background_enhance=True,
            face_upsample=True,
            upscale=2,
            codeformer_fidelity=settings.enhance_fidelity,
            api_name="/inference",
        )
        out = result.get("path") if isinstance(result, dict) else result
        if not out:
            raise RuntimeError("CodeFormer no devolvio imagen")
        return Path(out)

    return hf.call(run)


def enhance_avatar(force: bool = False) -> Path:
    base = settings.avatar_image
    original = base.with_name("avatar_original.jpg")

    if not base.exists():
        raise RuntimeError(
            f"Falta la imagen del avatar ({base}). Corre primero: python cli.py avatar"
        )
    if not settings.enhance_enabled:
        return base
    if original.exists() and not force:
        return base

    if not original.exists():
        shutil.copy2(base, original)
    source = original if force else base

    enhanced = _enhance(source)
    shutil.copy2(enhanced, base)
    return base
