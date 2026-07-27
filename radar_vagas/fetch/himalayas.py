from __future__ import annotations

from datetime import datetime, timezone

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

URL = "https://himalayas.app/jobs/api?limit=100"
FONTE = "himalayas"


def _iso(epoch: object) -> str | None:
    """`pubDate` da Himalayas vem em epoch inteiro, não ISO."""
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _faixa(j: dict) -> str | None:
    minimo, maximo = j.get("minSalary"), j.get("maxSalary")
    if not minimo and not maximo:
        return None
    moeda = j.get("currency") or ""
    periodo = j.get("salaryPeriod") or ""
    return f"{moeda} {minimo}-{maximo} {periodo}".strip()


def parse_himalayas(payload: dict) -> list[VagaBruta]:
    vagas: list[VagaBruta] = []
    for j in payload.get("jobs", []):
        guid = j.get("guid")
        titulo = j.get("title")
        if not guid or not titulo:
            continue
        restricoes = j.get("locationRestrictions") or []
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=guid,
                url=j.get("applicationLink") or guid,
                titulo=titulo,
                empresa=j.get("companyName"),
                geo_raw=", ".join(restricoes) if restricoes else None,
                geo_confiavel=True,
                publicado_em=_iso(j.get("pubDate")),
                descricao=j.get("description") or j.get("excerpt"),
                salario_raw=_faixa(j),
            )
        )
    return vagas


def buscar_himalayas() -> list[VagaBruta]:
    payload = get_json(URL)
    if not isinstance(payload, dict):
        raise FonteIndisponivel("himalayas: payload não é objeto")
    return parse_himalayas(payload)
