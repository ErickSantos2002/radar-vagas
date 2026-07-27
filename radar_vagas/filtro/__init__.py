from __future__ import annotations

from typing import Iterable

from radar_vagas.filtro.cargo import plausivel_data_engineer
from radar_vagas.filtro.geo import elegivel_brasil, sinal_no_titulo
from radar_vagas.filtro.presencial import e_presencial
from radar_vagas.models import VagaBruta

__all__ = [
    "aplicar_filtros",
    "e_presencial",
    "elegivel_brasil",
    "plausivel_data_engineer",
    "sinal_no_titulo",
]


def aplicar_filtros(
    vagas: Iterable[VagaBruta],
) -> tuple[list[VagaBruta], dict[str, bool | None]]:
    """Devolve (vagas aprovadas, mapa external_id -> elegibilidade geográfica).

    Descarta quem é explicitamente inelegível ou cujo cargo é implausível.
    Elegibilidade indefinida (None) passa: o scoring decide depois.
    """
    aprovadas: list[VagaBruta] = []
    geo_por_id: dict[str, bool | None] = {}
    for v in vagas:
        if e_presencial(v.titulo):
            continue
        geo = elegivel_brasil(v.geo_raw, confiavel=v.geo_confiavel)
        if geo is False and sinal_no_titulo(v.titulo):
            # O título contradiz o campo estruturado (ver sinal_no_titulo):
            # vira indefinido para o scoring julgar, em vez de descartar.
            geo = None
        if geo is False:
            continue
        if not plausivel_data_engineer(v.titulo, v.descricao):
            continue
        aprovadas.append(v)
        geo_por_id[v.external_id] = geo
    return aprovadas, geo_por_id
