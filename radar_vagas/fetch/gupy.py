from __future__ import annotations

from urllib.parse import quote

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

# O Gupy é o ATS dominante no Brasil. A API do portal aceita `workplaceType`
# como filtro server-side, então dá para garantir 100% remoto sem adivinhar a
# partir do texto — `isRemoteWork=true` NÃO serve, deixa passar híbrida.
BASE = "https://employability-portal.gupy.io/api/v1/jobs"
PAGINA = 100

# A busca é por texto no nome da vaga, então precisa de várias formulações.
TERMOS = (
    "engenheiro de dados",
    "engenharia de dados",
    "data engineer",
    "analytics engineer",
    "arquiteto de dados",
)

FONTE = "gupy"


def _url(termo: str, offset: int) -> str:
    return (
        f"{BASE}?jobName={quote(termo)}&workplaceType=remote"
        f"&limit={PAGINA}&offset={offset}"
    )


def parse_gupy(payload: dict) -> list[VagaBruta]:
    """Normaliza a resposta do portal, mantendo só o que é 100% remoto.

    O filtro de `workplaceType` é repetido aqui de propósito: a API já filtra,
    mas depender só do servidor significa que uma mudança silenciosa no
    parâmetro passaria vaga híbrida sem ninguém perceber.
    """
    vagas: list[VagaBruta] = []
    for j in payload.get("data", []):
        if j.get("workplaceType") != "remote":
            continue
        ident = j.get("id")
        titulo = j.get("name")
        url = j.get("jobUrl")
        if ident is None or not titulo or not url:
            continue
        local = ", ".join(
            p for p in (j.get("city"), j.get("state"), j.get("country")) if p
        )
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=str(ident),
                url=url,
                titulo=titulo.strip(),
                empresa=j.get("careerPageName"),
                geo_raw=local or "Brasil",
                geo_confiavel=True,
                publicado_em=j.get("publishedDate"),
                descricao=j.get("description"),
                salario_raw=None,
            )
        )
    return vagas


def buscar_gupy() -> list[VagaBruta]:
    """Busca cada termo, pagina, e deduplica pelo id da vaga.

    Uma vaga aparece em mais de um termo com frequência ("Engenheiro de Dados"
    casa com dois deles), então o dedupe local evita duplicata no mesmo lote.
    """
    vagas: list[VagaBruta] = []
    vistos: set[str] = set()
    for termo in TERMOS:
        offset = 0
        while True:
            payload = get_json(_url(termo, offset))
            if not isinstance(payload, dict):
                raise FonteIndisponivel("gupy: payload não é objeto")
            encontradas = parse_gupy(payload)
            for v in encontradas:
                if v.external_id not in vistos:
                    vistos.add(v.external_id)
                    vagas.append(v)

            paginacao = payload.get("pagination") or {}
            total = paginacao.get("total", 0)
            offset += PAGINA
            if offset >= total or not payload.get("data"):
                break
    return vagas
