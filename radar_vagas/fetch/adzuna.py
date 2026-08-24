"""Adzuna: a única agregadora testada com cobertura brasileira real.

As fontes internacionais do radar (Himalayas, WWR, RemoteOK) coletam muito e
aprovam quase nada: elas listam vagas que não contratam quem mora no Brasil.
A Adzuna tem índice brasileiro próprio, então entra para cobrir o mesmo terreno
da Gupy por outro caminho.

Duas limitações que valem saber antes de confiar no dado:

- `description` vem truncada. A Adzuna devolve um resumo do anúncio, não o
  texto inteiro, então a extração de skills rende menos aqui do que nas outras
  fontes. A vaga continua útil; o radar de skills é que enxerga menos.
- `salary_min` e `salary_max` às vezes são estimativa do modelo da Adzuna, não
  número informado pela empresa. Quando `salary_is_predicted` vier marcado, o
  salário é descartado: estimativa apresentada como fato vira decisão errada.

Precisa de credencial gratuita em https://developer.adzuna.com (1.000 chamadas
por mês). Sem as variáveis de ambiente a fonte se declara indisponível, e o
coletor segue com as outras.
"""

from __future__ import annotations

import os
from urllib.parse import urlencode

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

FONTE = "adzuna"
BASE = "https://api.adzuna.com/v1/api/jobs/br/search/1"

# Um termo por chamada. Três termos por coleta, semanal, cabe folgado no limite
# gratuito e cobre como as vagas brasileiras são anunciadas na prática.
TERMOS = ("engenheiro de dados", "data engineer", "analytics engineer")

RESULTADOS_POR_TERMO = 50


def _credenciais() -> tuple[str, str]:
    app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
    app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        raise FonteIndisponivel(
            "adzuna: defina ADZUNA_APP_ID e ADZUNA_APP_KEY "
            "(chave gratuita em https://developer.adzuna.com)"
        )
    return app_id, app_key


def montar_url(termo: str, app_id: str, app_key: str) -> str:
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTADOS_POR_TERMO,
        "what": termo,
        "content-type": "application/json",
    }
    return f"{BASE}?{urlencode(params)}"


def _salario(j: dict) -> str | None:
    """Só devolve salário informado pela empresa, nunca o estimado."""
    if str(j.get("salary_is_predicted", "")) == "1":
        return None
    minimo, maximo = j.get("salary_min"), j.get("salary_max")
    if minimo and maximo:
        return f"R$ {float(minimo):,.0f} - R$ {float(maximo):,.0f}".replace(",", ".")
    if minimo:
        return f"R$ {float(minimo):,.0f}".replace(",", ".")
    return None


def parse_adzuna(payload: dict) -> list[VagaBruta]:
    vagas: list[VagaBruta] = []
    for j in payload.get("results", []):
        ident = j.get("id")
        url = j.get("redirect_url")
        titulo = j.get("title")
        if ident is None or not url or not titulo:
            continue

        empresa = (j.get("company") or {}).get("display_name")
        local = (j.get("location") or {}).get("display_name")

        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=str(ident),
                url=url,
                titulo=titulo.strip(),
                empresa=empresa,
                geo_raw=local,
                # O índice é o brasileiro: a localização vem da própria vaga,
                # não de inferência do radar.
                geo_confiavel=True,
                publicado_em=j.get("created"),
                descricao=j.get("description"),
                salario_raw=_salario(j),
            )
        )
    return vagas


def buscar_adzuna() -> list[VagaBruta]:
    app_id, app_key = _credenciais()
    vagas: list[VagaBruta] = []
    vistos: set[str] = set()

    for termo in TERMOS:
        payload = get_json(montar_url(termo, app_id, app_key))
        if not isinstance(payload, dict):
            raise FonteIndisponivel(f"adzuna: payload não é objeto para '{termo}'")
        # Os termos se sobrepõem de propósito; deduplicar aqui evita entregar a
        # mesma vaga várias vezes ao filtro.
        for vaga in parse_adzuna(payload):
            if vaga.external_id not in vistos:
                vistos.add(vaga.external_id)
                vagas.append(vaga)

    return vagas
