from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from radar_vagas.config import CAMINHO_DB, PASTA_RELATORIOS
from radar_vagas.db import (
    conectar,
    criar_schema,
    inserir_vagas,
    registrar_run,
    total_coletadas,
)
from radar_vagas.fetch import coletar_tudo
from radar_vagas.filtro import aplicar_filtros
from radar_vagas.relatorio import (
    carregar_vagas,
    escrever,
    garantir_indice,
    gerar_markdown,
    semana_iso,
)
from radar_vagas.skills import contar_skills, gravar_skills


def _abrir() -> sqlite3.Connection:
    con = conectar(CAMINHO_DB)
    criar_schema(con)
    return con


def cmd_coletar(_: argparse.Namespace) -> int:
    vagas, erros = coletar_tudo()
    aprovadas, geo_por_id = aplicar_filtros(vagas)

    con = _abrir()
    novas = inserir_vagas(con, aprovadas, geo_por_id)
    gravar_skills(con, aprovadas)
    registrar_run(con, len(vagas), len(aprovadas), novas)

    print()
    print(f"coletadas    {len(vagas)}")
    print(f"aprovadas    {len(aprovadas)}")
    print(f"novas no db  {novas}")

    por_fonte: dict[str, list[int]] = {}
    for v in vagas:
        por_fonte.setdefault(v.fonte, [0, 0])[0] += 1
    for v in aprovadas:
        por_fonte.setdefault(v.fonte, [0, 0])[1] += 1

    print()
    print(f"{'fonte':<12} {'coletadas':>10} {'aprovadas':>10}")
    for fonte, (total, ok) in sorted(por_fonte.items(), key=lambda kv: -kv[1][1]):
        print(f"{fonte:<12} {total:>10} {ok:>10}")

    if erros:
        print("\nfontes com erro:")
        for e in erros:
            print(f"  {e}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    con = _abrir()
    linhas = con.execute(
        """
        SELECT v.id, v.fonte, COALESCE(v.empresa, '-'), v.titulo,
               CASE v.geo_ok WHEN 1 THEN 'sim' WHEN 0 THEN 'nao' ELSE '?' END,
               v.url
        FROM vagas v WHERE v.status = ?
        ORDER BY v.fonte, v.empresa, v.titulo
        """,
        (args.status,),
    ).fetchall()

    if not linhas:
        print(f"nenhuma vaga com status '{args.status}'")
        return 0

    print(f"{'id':>4}  {'br':<3} {'fonte':<10} {'empresa':<22} titulo")
    print("-" * 96)
    for vid, fonte, empresa, titulo, geo, url in linhas:
        print(f"{vid:>4}  {geo:<3} {fonte:<10} {empresa[:21]:<22} {titulo[:44]}")
        if args.links:
            print(f"      {url}")
    print(f"\n{len(linhas)} vaga(s). Use `descartar <id>` ou `aplicada <id>`.")
    return 0


def _mudar_status(con: sqlite3.Connection, vaga_id: int, status: str) -> int:
    cur = con.execute("UPDATE vagas SET status = ? WHERE id = ?", (status, vaga_id))
    con.commit()
    if cur.rowcount == 0:
        print(f"vaga {vaga_id} não encontrada")
        return 1
    print(f"vaga {vaga_id} -> {status}")
    return 0


def cmd_descartar(args: argparse.Namespace) -> int:
    return _mudar_status(_abrir(), args.id, "descartada")


def cmd_aplicada(args: argparse.Namespace) -> int:
    return _mudar_status(_abrir(), args.id, "aplicada")


def cmd_web(args: argparse.Namespace) -> int:
    """Sobe a triagem local e abre no navegador."""
    import threading
    import webbrowser

    from radar_vagas.web import criar_app

    url = f"http://127.0.0.1:{args.porta}/"
    print(f"triagem em {url}   (ctrl+c para parar)")
    if not args.sem_navegador:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    criar_app(CAMINHO_DB).run(host="127.0.0.1", port=args.porta, debug=False)
    return 0


def cmd_relatorio(args: argparse.Namespace) -> int:
    con = _abrir()
    total = total_coletadas(con)
    vagas = carregar_vagas(con)
    contagem = contar_skills(con)
    semana = args.semana or semana_iso()

    destino = escrever(semana, gerar_markdown(semana, vagas, contagem, total), args.pasta)
    indice = garantir_indice(args.pasta)
    print(f"relatorio  {destino}")
    print(f"indice     {indice}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    p = argparse.ArgumentParser(prog="radar-vagas", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("coletar", help="busca as fontes, filtra e grava").set_defaults(
        func=cmd_coletar
    )

    pr = sub.add_parser("review", help="lista as vagas para revisão")
    pr.add_argument("--status", default="pendente")
    pr.add_argument("--links", action="store_true", help="mostra a URL de cada vaga")
    pr.set_defaults(func=cmd_review)

    pd = sub.add_parser("descartar", help="marca uma vaga como descartada")
    pd.add_argument("id", type=int)
    pd.set_defaults(func=cmd_descartar)

    pa = sub.add_parser("aplicada", help="marca uma vaga como aplicada")
    pa.add_argument("id", type=int)
    pa.set_defaults(func=cmd_aplicada)

    pw = sub.add_parser("web", help="abre a triagem no navegador")
    pw.add_argument("--porta", type=int, default=5111)
    pw.add_argument("--sem-navegador", action="store_true")
    pw.set_defaults(func=cmd_web)

    prel = sub.add_parser("relatorio", help="escreve a nota da semana no vault")
    prel.add_argument("--semana", help="ex: 2026-W31 (default: semana atual)")
    prel.add_argument(
        "--pasta", type=Path, help=f"destino (default: {PASTA_RELATORIOS})"
    )
    prel.set_defaults(func=cmd_relatorio)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
