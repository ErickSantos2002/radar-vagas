from __future__ import annotations

import re

_TITULO = re.compile(
    r"\b("
    # inglês
    r"data\s+engineer|analytics\s+engineer|data\s+platform|"
    r"data\s+infra(structure)?|dataops|data\s+pipeline|"
    r"etl\s+(developer|engineer)|data\s+warehouse\s+engineer|"
    # português — o Gupy publica quase tudo assim, e sem isto as vagas
    # brasileiras seriam todas descartadas. O `(?:\(a\))?` cobre a forma
    # "Engenheiro(a) de Dados", comum em anúncio brasileiro.
    # `eng\.?\s+de\s+dados` cobre a abreviação "Eng de Dados", que aparece em
    # vaga real no Gupy e não casaria com `engenheir\w*`.
    r"engenheir\w*(?:\(a\))?\s+de\s+dados|"
    r"eng\.?\s+de\s+dados|"
    r"arquitetura\s+de\s+dados|"
    r"engenharia\s+de\s+dados|"
    r"arquitet\w*(?:\(a\))?\s+de\s+dados|"
    r"plataforma\s+de\s+dados"
    r")\b",
    re.IGNORECASE,
)

_STACK = (
    "dbt",
    "airflow",
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    "spark",
    "kafka",
    "dagster",
    "fivetran",
    "etl",
    "data warehouse",
    "data lake",
    "data pipeline",
)

_STACK_RE = {t: re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE) for t in _STACK}

MIN_TERMOS = 3


def plausivel_data_engineer(titulo: str, descricao: str | None) -> bool:
    """True se a vaga pode ser de Data Engineer e merece ir para o scoring.

    Aprova por título, ou por menção a MIN_TERMOS termos distintos da stack de
    dados na descrição — muita vaga boa se chama "Software Engineer, Data
    Platform" e não casaria só pelo título.
    """
    if _TITULO.search(titulo or ""):
        return True
    if not descricao:
        return False
    distintos = sum(1 for padrao in _STACK_RE.values() if padrao.search(descricao))
    return distintos >= MIN_TERMOS
