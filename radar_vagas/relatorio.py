from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from radar_vagas.config import PASTA_RELATORIOS


@dataclass(frozen=True, slots=True)
class Vaga:
    """Uma linha do relatório, já com as skills anexadas."""

    fonte: str
    empresa: str | None
    titulo: str
    geo_raw: str | None
    geo_ok: int | None
    url: str
    skills: list[str] = field(default_factory=list)


def semana_iso(quando: str | None = None) -> str:
    """'2026-07-27T10:00:00+00:00' -> '2026-W31'."""
    d = datetime.fromisoformat(quando).date() if quando else date.today()
    ano, semana, _ = d.isocalendar()
    return f"{ano}-W{semana:02d}"


def nome_arquivo(semana: str) -> str:
    return f"Semana-{semana}.md"


def _regiao(v: Vaga) -> str:
    if v.geo_ok == 1:
        return v.geo_raw or "aceita Brasil"
    if v.geo_ok is None:
        return f"a confirmar ({v.geo_raw})" if v.geo_raw else "a confirmar"
    return v.geo_raw or "restrita"


def gerar_markdown(
    semana: str,
    vagas: list[Vaga],
    contagem: Counter[str],
    total_coletadas: int,
) -> str:
    """Monta a nota da semana seguindo as convenções do vault.

    Sem frontmatter, título direto, prosa curta, e `## Notas relacionadas` no
    fim linkando a meta que o radar serve.
    """
    linhas: list[str] = [f"# Radar de Vagas — Semana {semana}", ""]

    if vagas:
        linhas.append(
            f"Das {total_coletadas} vagas coletadas nas cinco fontes, "
            f"{len(vagas)} passaram o filtro e estão listadas abaixo. "
            "A elegibilidade marcada como *a confirmar* é onde a fonte não "
            "declara restrição de forma confiável — vale abrir o anúncio."
        )
    else:
        linhas.append(
            f"Nenhuma das {total_coletadas} vagas coletadas passou o filtro "
            "esta semana. Se isso repetir, o filtro de cargo está estreito "
            "demais para o volume das fontes."
        )
    linhas.append("")

    if vagas:
        linhas += ["## Vagas para revisar", ""]
        for v in sorted(vagas, key=lambda x: (x.fonte, x.empresa or "", x.titulo)):
            empresa = f"**{v.empresa}** — " if v.empresa else ""
            linhas.append(f"- {empresa}[{v.titulo}]({v.url})")
            detalhe = f"  {v.fonte} · {_regiao(v)}"
            if v.skills:
                detalhe += f" · {', '.join(sorted(v.skills))}"
            linhas += [detalhe, ""]

    if contagem:
        linhas += ["## O que o mercado está pedindo", ""]
        total = len(vagas) or 1
        for skill, n in contagem.most_common(15):
            pct = round(100 * n / total)
            linhas.append(f"- `{skill}` — {n} de {total} vagas ({pct}%)")
        linhas += [
            "",
            "Contagem por regex sobre a descrição, então ela mede *menção* e "
            "não *exigência* — uma skill citada como diferencial conta igual. "
            "O scoring da Fase 4 separa os dois.",
            "",
        ]

    linhas += [
        "## Notas relacionadas",
        "",
        "- [[Radar de Vagas|Radar de Vagas]] — índice de todas as semanas",
        "- [[../Trabalho-Remoto|Trabalho Remoto]] — a meta que este radar serve",
        "- [[../../Trabalho/Como-Vejo-o-Trabalho|Como Vejo o Trabalho]] — "
        "o que dá energia e o que drena",
    ]
    return "\n".join(linhas) + "\n"


def carregar_vagas(con: sqlite3.Connection, desde: str | None = None) -> list[Vaga]:
    """Vagas pendentes, com as skills já agregadas por vaga."""
    sql = """
        SELECT v.id, v.fonte, v.empresa, v.titulo, v.geo_raw, v.geo_ok, v.url
        FROM vagas v
        WHERE v.status = 'pendente'
    """
    params: tuple[str, ...] = ()
    if desde:
        sql += " AND v.visto_em >= ?"
        params = (desde,)

    vagas: list[Vaga] = []
    for vid, fonte, empresa, titulo, geo_raw, geo_ok, url in con.execute(sql, params):
        skills = [
            s
            for (s,) in con.execute(
                "SELECT skill FROM skills WHERE vaga_id = ?", (vid,)
            )
        ]
        vagas.append(
            Vaga(
                fonte=fonte,
                empresa=empresa,
                titulo=titulo,
                geo_raw=geo_raw,
                geo_ok=geo_ok,
                url=url,
                skills=skills,
            )
        )
    return vagas


def escrever(semana: str, conteudo: str, pasta: Path | None = None) -> Path:
    destino = (pasta or PASTA_RELATORIOS) / nome_arquivo(semana)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    return destino


INDICE = """# Radar de Vagas

Relatório semanal do [radar-vagas](https://github.com/ErickSantos2002/radar-vagas):
vagas de Data Engineer abertas em cinco boards internacionais que aceitam
contratação no Brasil, e o que essas vagas estão pedindo.

Cada nota `Semana-AAAA-Wnn` é um retrato daquela semana. A leitura útil é
comparar semanas: qual skill subiu, qual faixa salarial se firmou, quais
empresas voltaram a abrir vaga.

## Semanas

## Notas relacionadas

- [[../Trabalho-Remoto|Trabalho Remoto]] — a meta que este radar serve
- [[../../Erick|Erick]] — índice geral
"""


def garantir_indice(pasta: Path | None = None) -> Path:
    """Cria a nota-índice se ainda não existir, e lista as semanas presentes."""
    base = pasta or PASTA_RELATORIOS
    base.mkdir(parents=True, exist_ok=True)
    destino = base / "Radar de Vagas.md"
    if not destino.exists():
        destino.write_text(INDICE, encoding="utf-8")

    semanas = sorted(
        (p.stem for p in base.glob("Semana-*.md")),
        reverse=True,
    )
    texto = destino.read_text(encoding="utf-8")
    bloco = "\n".join(f"- [[{s}|{s.replace('Semana-', '')}]]" for s in semanas)
    inicio = texto.index("## Semanas") + len("## Semanas")
    fim = texto.index("## Notas relacionadas")
    destino.write_text(
        texto[:inicio] + "\n\n" + bloco + "\n\n" + texto[fim:], encoding="utf-8"
    )
    return destino
