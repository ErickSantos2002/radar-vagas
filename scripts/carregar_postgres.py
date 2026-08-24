"""Carga do SQLite operacional para o Postgres analítico.

O radar grava em SQLite porque a coleta é local e single-writer. A análise
mora em outro lugar: o dbt precisa de um banco onde dá para modelar, testar e
versionar transformação. Este script é o EL entre os dois — extrai as tabelas
brutas e as reescreve no schema `raw`, sem transformar nada. Toda regra de
negócio fica nos modelos dbt, não aqui.

Recarga completa por tabela: o volume é pequeno (centenas de linhas por
coleta) e refazer do zero elimina a classe de bug mais chata de ingestão
incremental, que é divergência silenciosa entre origem e destino.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

RAIZ = Path(__file__).resolve().parent.parent
SQLITE = RAIZ / "vagas.db"

# origem no SQLite -> destino no Postgres, com o DDL do destino.
TABELAS: dict[str, tuple[str, str]] = {
    "vagas": (
        "raw.vagas",
        """
        CREATE TABLE IF NOT EXISTS raw.vagas (
          id           bigint PRIMARY KEY,
          fonte        text NOT NULL,
          external_id  text NOT NULL,
          url          text NOT NULL,
          titulo       text NOT NULL,
          empresa      text,
          geo_raw      text,
          geo_ok       int,
          publicado_em text,
          visto_em     text NOT NULL,
          descricao    text,
          salario_raw  text,
          status       text NOT NULL,
          tentativas   int NOT NULL
        )""",
    ),
    "skills": (
        "raw.skills",
        """
        CREATE TABLE IF NOT EXISTS raw.skills (
          vaga_id bigint NOT NULL,
          skill   text NOT NULL,
          PRIMARY KEY (vaga_id, skill)
        )""",
    ),
    "runs": (
        "raw.runs",
        """
        CREATE TABLE IF NOT EXISTS raw.runs (
          id        bigint PRIMARY KEY,
          quando    text NOT NULL,
          coletadas int NOT NULL,
          aprovadas int NOT NULL,
          novas     int NOT NULL
        )""",
    ),
    "scores": (
        "raw.scores",
        """
        CREATE TABLE IF NOT EXISTS raw.scores (
          vaga_id     bigint PRIMARY KEY,
          nota        int NOT NULL,
          senioridade text,
          contrato    text,
          salario_min double precision,
          salario_max double precision,
          moeda       text,
          periodo     text,
          motivo      text,
          scored_em   text NOT NULL
        )""",
    ),
}


def _dsn() -> str:
    faltando = [
        v
        for v in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT")
        if not os.environ.get(v)
    ]
    if faltando:
        sys.exit(
            "variáveis de ambiente ausentes: "
            + ", ".join(faltando)
            + "\ncarregue o .env antes de rodar (ver README)"
        )
    return (
        f"host=127.0.0.1 port={os.environ['POSTGRES_PORT']} "
        f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


def carregar() -> int:
    if not SQLITE.exists():
        sys.exit(f"{SQLITE} não existe — rode `radar-vagas coletar` antes")

    origem = sqlite3.connect(f"file:{SQLITE}?mode=ro", uri=True)
    origem.row_factory = sqlite3.Row
    total = 0

    with psycopg2.connect(_dsn()) as destino, destino.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for tabela, (alvo, ddl) in TABELAS.items():
            cur.execute(ddl)
            linhas = origem.execute(f"SELECT * FROM {tabela}").fetchall()
            cur.execute(f"TRUNCATE {alvo}")
            if linhas:
                colunas = linhas[0].keys()
                execute_values(
                    cur,
                    f"INSERT INTO {alvo} ({', '.join(colunas)}) VALUES %s",
                    [tuple(linha) for linha in linhas],
                )
            print(f"{alvo:<12} {len(linhas):>6} linhas")
            total += len(linhas)

    origem.close()
    return total


if __name__ == "__main__":
    print(f"\ntotal: {carregar()} linhas carregadas no Postgres")
