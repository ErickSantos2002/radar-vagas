from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from radar_vagas.models import VagaBruta

SCHEMA = """
CREATE TABLE IF NOT EXISTS vagas (
  id           INTEGER PRIMARY KEY,
  fonte        TEXT NOT NULL,
  external_id  TEXT NOT NULL,
  url          TEXT NOT NULL,
  titulo       TEXT NOT NULL,
  empresa      TEXT,
  geo_raw      TEXT,
  geo_ok       INTEGER,
  publicado_em TEXT,
  visto_em     TEXT NOT NULL,
  descricao    TEXT,
  salario_raw  TEXT,
  status       TEXT NOT NULL DEFAULT 'pendente',
  tentativas   INTEGER NOT NULL DEFAULT 0,
  UNIQUE (fonte, external_id)
);

CREATE TABLE IF NOT EXISTS scores (
  vaga_id     INTEGER PRIMARY KEY REFERENCES vagas(id),
  nota        INTEGER NOT NULL,
  senioridade TEXT,
  contrato    TEXT,
  salario_min REAL,
  salario_max REAL,
  moeda       TEXT,
  periodo     TEXT,
  motivo      TEXT,
  scored_em   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
  vaga_id INTEGER NOT NULL REFERENCES vagas(id),
  skill   TEXT NOT NULL,
  PRIMARY KEY (vaga_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_vagas_status ON vagas(status);
CREATE INDEX IF NOT EXISTS idx_vagas_visto  ON vagas(visto_em);
"""


def conectar(caminho: str | Path = "vagas.db") -> sqlite3.Connection:
    con = sqlite3.connect(caminho)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def criar_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()


def inserir_vagas(
    con: sqlite3.Connection,
    vagas: Iterable[VagaBruta],
    geo_por_id: dict[str, bool | None],
) -> int:
    """Insere vagas novas. Retorna quantas foram de fato inseridas.

    `geo_por_id` mapeia `external_id` -> elegibilidade (True/False/None).
    Conflito em (fonte, external_id) é ignorado silenciosamente: é o dedupe.
    """
    agora = datetime.now(timezone.utc).isoformat()
    inseridas = 0
    for v in vagas:
        geo = geo_por_id.get(v.external_id)
        cur = con.execute(
            """
            INSERT OR IGNORE INTO vagas
              (fonte, external_id, url, titulo, empresa, geo_raw, geo_ok,
               publicado_em, visto_em, descricao, salario_raw, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente')
            """,
            (
                v.fonte,
                v.external_id,
                v.url,
                v.titulo,
                v.empresa,
                v.geo_raw,
                None if geo is None else int(geo),
                v.publicado_em,
                agora,
                v.descricao,
                v.salario_raw,
            ),
        )
        inseridas += cur.rowcount
    con.commit()
    return inseridas
