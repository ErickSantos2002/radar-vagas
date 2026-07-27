import pytest

from radar_vagas.db import conectar, criar_schema, inserir_vagas
from radar_vagas.models import VagaBruta
from radar_vagas.skills import gravar_skills
from radar_vagas.web import criar_app


def _vaga(external_id: str, titulo: str = "Engenheiro de Dados") -> VagaBruta:
    return VagaBruta(
        fonte="gupy",
        external_id=external_id,
        url=f"https://g.test/{external_id}",
        titulo=titulo,
        empresa="Acme",
        geo_raw="Brasil",
        geo_confiavel=True,
        publicado_em="2026-07-27T00:00:00+00:00",
        descricao="Pipelines com airflow e dbt em snowflake.",
        salario_raw=None,
    )


@pytest.fixture()
def app(tmp_path):
    caminho = tmp_path / "t.db"
    con = conectar(caminho)
    criar_schema(con)
    vagas = [_vaga("1"), _vaga("2", "Analytics Engineer"), _vaga("3")]
    inserir_vagas(con, vagas, {v.external_id: True for v in vagas})
    gravar_skills(con, vagas)
    con.close()
    aplicacao = criar_app(caminho)
    aplicacao.config.update(TESTING=True)
    return aplicacao


def test_lista_as_pendentes(app) -> None:
    resp = app.test_client().get("/")
    assert resp.status_code == 200
    corpo = resp.get_data(as_text=True)
    assert "Engenheiro de Dados" in corpo
    assert "Analytics Engineer" in corpo
    assert "Acme" in corpo


def test_mostra_contador_de_pendentes(app) -> None:
    corpo = app.test_client().get("/").get_data(as_text=True)
    assert 'id="restam"' in corpo
    assert ">3<" in corpo


def test_marca_como_interessante(app) -> None:
    cliente = app.test_client()
    resp = cliente.post("/vagas/1/decidir", json={"decisao": "sim"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "interessante"
    assert resp.get_json()["restam"] == 2


def test_marca_como_descartada(app) -> None:
    cliente = app.test_client()
    resp = cliente.post("/vagas/2/decidir", json={"decisao": "nao"})
    assert resp.get_json()["status"] == "descartada"


def test_desfaz_decisao(app) -> None:
    cliente = app.test_client()
    cliente.post("/vagas/1/decidir", json={"decisao": "sim"})
    resp = cliente.post("/vagas/1/decidir", json={"decisao": "pendente"})
    assert resp.get_json()["status"] == "pendente"
    assert resp.get_json()["restam"] == 3


def test_decisao_invalida_e_rejeitada(app) -> None:
    resp = app.test_client().post("/vagas/1/decidir", json={"decisao": "talvez"})
    assert resp.status_code == 400


def test_vaga_inexistente(app) -> None:
    resp = app.test_client().post("/vagas/999/decidir", json={"decisao": "sim"})
    assert resp.status_code == 404


def test_skills_aparecem_na_pagina(app) -> None:
    corpo = app.test_client().get("/").get_data(as_text=True)
    assert "airflow" in corpo
    assert "dbt" in corpo


def test_filtro_por_status(app) -> None:
    cliente = app.test_client()
    cliente.post("/vagas/1/decidir", json={"decisao": "sim"})
    corpo = cliente.get("/?status=interessante").get_data(as_text=True)
    assert "Engenheiro de Dados" in corpo
    assert "Analytics Engineer" not in corpo
