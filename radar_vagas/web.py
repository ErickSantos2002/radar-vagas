from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

from radar_vagas.config import CAMINHO_DB

# O que cada botão grava. "descartada" e "interessante" são simétricos de
# propósito: rejeitar não é erro, é a decisão barata que o Erick vai tomar
# dezenas de vezes por semana.
DECISOES = {
    "sim": "interessante",
    "nao": "descartada",
    "pendente": "pendente",
}


def criar_app(caminho_db: Path | str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["CAMINHO_DB"] = Path(caminho_db or CAMINHO_DB)

    def con() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["CAMINHO_DB"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def fechar(_exc: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def pendentes() -> int:
        return con().execute(
            "SELECT COUNT(*) FROM vagas WHERE status = 'pendente'"
        ).fetchone()[0]

    @app.get("/")
    def index() -> str:
        status = request.args.get("status", "pendente")
        linhas = con().execute(
            """
            SELECT id, fonte, empresa, titulo, geo_raw, geo_ok, url,
                   publicado_em, salario_raw, descricao, status
            FROM vagas WHERE status = ?
            ORDER BY fonte, empresa, titulo
            """,
            (status,),
        ).fetchall()

        vagas = []
        for linha in linhas:
            skills = [
                s[0]
                for s in con().execute(
                    "SELECT skill FROM skills WHERE vaga_id = ? ORDER BY skill",
                    (linha["id"],),
                )
            ]
            vagas.append({**dict(linha), "skills": skills})

        contagens = dict(
            con().execute("SELECT status, COUNT(*) FROM vagas GROUP BY status")
        )
        return render_template(
            "triagem.html",
            vagas=vagas,
            status=status,
            restam=contagens.get("pendente", 0),
            contagens=contagens,
        )

    @app.post("/vagas/<int:vaga_id>/decidir")
    def decidir(vaga_id: int):
        decisao = (request.get_json(silent=True) or {}).get("decisao")
        if decisao not in DECISOES:
            return jsonify(erro=f"decisão inválida: {decisao!r}"), 400

        novo = DECISOES[decisao]
        cur = con().execute(
            "UPDATE vagas SET status = ? WHERE id = ?", (novo, vaga_id)
        )
        con().commit()
        if cur.rowcount == 0:
            return jsonify(erro=f"vaga {vaga_id} não existe"), 404
        return jsonify(status=novo, restam=pendentes())

    return app
