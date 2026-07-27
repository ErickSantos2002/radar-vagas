from __future__ import annotations

import logging
from typing import Callable

from radar_vagas.fetch.himalayas import buscar_himalayas
from radar_vagas.fetch.hn import buscar_hn
from radar_vagas.fetch.remoteok import buscar_remoteok
from radar_vagas.fetch.remotive import buscar_remotive
from radar_vagas.fetch.wwr import buscar_wwr
from radar_vagas.models import VagaBruta

log = logging.getLogger(__name__)

__all__ = ["FONTES", "coletar_tudo"]

FONTES: dict[str, Callable[[], list[VagaBruta]]] = {
    "remotive": buscar_remotive,
    "remoteok": buscar_remoteok,
    "wwr": buscar_wwr,
    "himalayas": buscar_himalayas,
    "hn": buscar_hn,
}


def coletar_tudo() -> tuple[list[VagaBruta], list[str]]:
    """Coleta de todas as fontes. Fonte que falhar é registrada e pulada.

    Nenhuma fonte pode derrubar o run — é por isso que o `except` é amplo.
    """
    vagas: list[VagaBruta] = []
    erros: list[str] = []
    for nome, buscar in FONTES.items():
        try:
            encontradas = buscar()
        except Exception as exc:
            log.warning("fonte %s falhou: %s", nome, exc)
            erros.append(f"{nome}: {exc}")
            continue
        log.info("fonte %s: %d vagas", nome, len(encontradas))
        vagas.extend(encontradas)
    return vagas, erros
