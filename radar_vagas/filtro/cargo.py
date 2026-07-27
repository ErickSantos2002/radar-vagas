from __future__ import annotations

import re

_TITULO = re.compile(
    r"\b("
    r"data\s+engineer|analytics\s+engineer|data\s+platform|"
    r"data\s+infra(structure)?|dataops|data\s+pipeline|"
    r"etl\s+(developer|engineer)|data\s+warehouse\s+engineer"
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
