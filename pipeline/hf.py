"""Helper para llamar Spaces de Hugging Face con reintentos y SSL tolerante.

El entorno puede tener un proxy con certificado propio (MITM); por eso se usa
ssl_verify=False para los Spaces publicos, junto con reintentos.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, TypeVar

from .config import settings

T = TypeVar("T")


def client(space: str):
    from gradio_client import Client

    return Client(
        space,
        verbose=False,
        token=settings.hf_token or None,
        ssl_verify=False,
    )


def handle(path: Path):
    try:
        from gradio_client import handle_file

        return handle_file(str(path))
    except Exception:  # noqa: BLE001
        return str(path)


def call(fn: Callable[[], T], retries: int = 3, delay: float = 2.0) -> T:
    last: Exception | None = None
    for i in range(retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if i < retries - 1:
                time.sleep(delay * (i + 1))
    assert last is not None
    raise last
