from __future__ import annotations

import requests

TIMEOUT = 20
UA = "radar-vagas/0.1 (+https://github.com/ErickSantos2002/radar-vagas)"


class FonteIndisponivel(Exception):
    """A fonte não respondeu, respondeu erro, ou devolveu algo inesperado."""


def _get(url: str) -> requests.Response:
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FonteIndisponivel(f"{url}: {exc}") from exc
    return resp


def get_json(url: str) -> object:
    resp = _get(url)
    try:
        return resp.json()
    except ValueError as exc:
        raise FonteIndisponivel(f"{url}: resposta não é JSON") from exc


def get_text(url: str) -> str:
    return _get(url).text
