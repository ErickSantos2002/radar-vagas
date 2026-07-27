from __future__ import annotations

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

URL = "https://remotive.com/api/remote-jobs?category=data&limit=100"
FONTE = "remotive"


def parse_remotive(payload: dict) -> list[VagaBruta]:
    vagas: list[VagaBruta] = []
    for j in payload.get("jobs", []):
        ident = j.get("id")
        url = j.get("url")
        titulo = j.get("title")
        if ident is None or not url or not titulo:
            continue
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=str(ident),
                url=url,
                titulo=titulo,
                empresa=j.get("company_name"),
                geo_raw=j.get("candidate_required_location"),
                geo_confiavel=True,
                publicado_em=j.get("publication_date"),
                descricao=j.get("description"),
                salario_raw=j.get("salary") or None,
            )
        )
    return vagas


def buscar_remotive() -> list[VagaBruta]:
    payload = get_json(URL)
    if not isinstance(payload, dict):
        raise FonteIndisponivel("remotive: payload não é objeto")
    return parse_remotive(payload)
