from __future__ import annotations

import re
import sqlite3
from collections import Counter
from typing import Iterable

from radar_vagas.models import VagaBruta

# canônico -> variações aceitas. Sem isto o radar conta "Apache Airflow",
# "airflow" e "AIRFLOW" como três skills diferentes.
VOCABULARIO: dict[str, tuple[str, ...]] = {
    # linguagens
    "python": ("python",),
    "sql": ("sql",),
    "scala": ("scala",),
    "java": ("java",),
    "r": ("r",),
    "go": ("go", "golang"),
    "typescript": ("typescript", "ts"),
    # orquestração e transformação
    "airflow": ("airflow", "apache airflow"),
    "dbt": ("dbt",),
    "dagster": ("dagster",),
    "prefect": ("prefect",),
    "luigi": ("luigi",),
    "fivetran": ("fivetran",),
    "airbyte": ("airbyte",),
    # armazém e lago
    "snowflake": ("snowflake",),
    "bigquery": ("bigquery", "big query"),
    "redshift": ("redshift",),
    "databricks": ("databricks",),
    "synapse": ("synapse",),
    "delta lake": ("delta lake", "deltalake"),
    "iceberg": ("iceberg", "apache iceberg"),
    # processamento
    "spark": ("spark", "apache spark", "pyspark"),
    "kafka": ("kafka", "apache kafka"),
    "flink": ("flink", "apache flink"),
    "beam": ("apache beam",),
    # bancos
    "postgresql": ("postgresql", "postgres"),
    "mysql": ("mysql",),
    "mongodb": ("mongodb", "mongo"),
    "cassandra": ("cassandra",),
    "elasticsearch": ("elasticsearch", "elastic search"),
    "clickhouse": ("clickhouse",),
    # nuvem
    "aws": ("aws", "amazon web services"),
    "gcp": ("gcp", "google cloud platform", "google cloud"),
    "azure": ("azure",),
    # infra
    "docker": ("docker",),
    "kubernetes": ("kubernetes", "k8s"),
    "terraform": ("terraform",),
    "ci/cd": ("ci/cd", "cicd"),
    # bi
    "looker": ("looker",),
    "tableau": ("tableau",),
    "power bi": ("power bi", "powerbi"),
    "metabase": ("metabase",),
    # conceitos
    "etl": ("etl", "elt"),
    "data warehouse": ("data warehouse", "data warehousing"),
    "data lake": ("data lake",),
    "data modeling": ("data modeling", "data modelling", "dimensional modeling"),
    "streaming": ("streaming", "real-time data"),
}

_PADROES: dict[str, re.Pattern[str]] = {
    canonico: re.compile(
        "|".join(rf"(?<![\w/]){re.escape(v)}(?![\w/])" for v in variacoes),
        re.IGNORECASE,
    )
    for canonico, variacoes in VOCABULARIO.items()
}


def extrair_skills(descricao: str | None) -> set[str]:
    """Skills canônicas mencionadas na descrição.

    É a versão sem LLM do radar (Fase 2). O scoring da Fase 4 refina isto,
    porque regex não distingue "usamos dbt" de "dbt é um diferencial".
    """
    if not descricao:
        return set()
    return {
        canonico
        for canonico, padrao in _PADROES.items()
        if padrao.search(descricao)
    }


def gravar_skills(con: sqlite3.Connection, vagas: Iterable[VagaBruta]) -> int:
    """Grava as skills das vagas já persistidas. Idempotente."""
    gravadas = 0
    for v in vagas:
        linha = con.execute(
            "SELECT id FROM vagas WHERE fonte = ? AND external_id = ?",
            (v.fonte, v.external_id),
        ).fetchone()
        if linha is None:
            continue
        for skill in extrair_skills(v.descricao):
            cur = con.execute(
                "INSERT OR IGNORE INTO skills (vaga_id, skill) VALUES (?, ?)",
                (linha[0], skill),
            )
            gravadas += cur.rowcount
    con.commit()
    return gravadas


def contar_skills(
    con: sqlite3.Connection, desde: str | None = None
) -> Counter[str]:
    """Quantas vagas pedem cada skill. `desde` filtra por `visto_em` (ISO)."""
    sql = """
        SELECT s.skill, COUNT(DISTINCT s.vaga_id)
        FROM skills s JOIN vagas v ON v.id = s.vaga_id
        WHERE v.status != 'descartada'
    """
    params: tuple[str, ...] = ()
    if desde:
        sql += " AND v.visto_em >= ?"
        params = (desde,)
    sql += " GROUP BY s.skill"
    return Counter(dict(con.execute(sql, params).fetchall()))
