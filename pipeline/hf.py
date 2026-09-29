"""Helper para llamar Spaces de Hugging Face con reintentos y SSL tolerante.

Esta PC sale a internet por un proxy con certificado propio (MITM), por lo que
la verificacion SSL debe desactivarse (HF_SSL_VERIFY=false en .env). En una red
normal (casa) se puede activar: HF_SSL_VERIFY=true.
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
        ssl_verify=settings.hf_ssl_verify,
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
