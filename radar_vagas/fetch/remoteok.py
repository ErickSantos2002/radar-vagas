from __future__ import annotations

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

URL = "https://remoteok.com/api"
FONTE = "remoteok"


def parse_remoteok(payload: list) -> list[VagaBruta]:
    """Normaliza o array da RemoteOK.

    O primeiro elemento é metadata (`last_updated`, `legal`), não uma vaga.
    O campo `location` é a cidade da empresa e não restrição de contratação,
    por isso `geo_confiavel=False`.
    """
    vagas: list[VagaBruta] = []
    for j in payload:
        if not isinstance(j, dict) or "legal" in j:
            continue
        ident = j.get("id")
        titulo = j.get("position")
        url = j.get("url") or j.get("apply_url")
        if ident is None or not titulo or not url:
            continue
        faixa = None
        if j.get("salary_min") and str(j["salary_min"]) != "0":
            faixa = f"{j.get('salary_min')}-{j.get('salary_max')}"
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=str(ident),
                url=url,
                titulo=titulo,
                empresa=j.get("company"),
                geo_raw=j.get("location"),
                geo_confiavel=False,
                publicado_em=j.get("date"),
                descricao=j.get("description"),
                salario_raw=faixa,
            )
        )
    return vagas


def buscar_remoteok() -> list[VagaBruta]:
    payload = get_json(URL)
    if not isinstance(payload, list):
        raise FonteIndisponivel("remoteok: payload não é lista")
    return parse_remoteok(payload)
