from radar_vagas.db import conectar, criar_schema, inserir_vagas
from radar_vagas.models import VagaBruta


def _vaga(external_id: str = "1", fonte: str = "remotive") -> VagaBruta:
    return VagaBruta(
        fonte=fonte,
        external_id=external_id,
        url="https://exemplo.test/1",
        titulo="Data Engineer",
        empresa="Acme",
        geo_raw="Worldwide",
        geo_confiavel=True,
        publicado_em="2026-07-20T00:00:00+00:00",
        descricao="dbt airflow snowflake",
        salario_raw="$5k-7k",
    )


def test_insere_e_persiste() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    assert inserir_vagas(con, [_vaga()], {"1": True}) == 1
    linha = con.execute("SELECT titulo, geo_ok, status FROM vagas").fetchone()
    assert linha == ("Data Engineer", 1, "pendente")


def test_dedupe_mesma_fonte_mesmo_id() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    inserir_vagas(con, [_vaga()], {"1": True})
    assert inserir_vagas(con, [_vaga()], {"1": True}) == 0
    assert con.execute("SELECT COUNT(*) FROM vagas").fetchone()[0] == 1


def test_mesmo_id_em_fontes_diferentes_nao_deduplica() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    inserir_vagas(con, [_vaga(fonte="remotive")], {"1": True})
    inserir_vagas(con, [_vaga(fonte="remoteok")], {"1": True})
    assert con.execute("SELECT COUNT(*) FROM vagas").fetchone()[0] == 2


def test_geo_indefinido_grava_null() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    inserir_vagas(con, [_vaga()], {"1": None})
    assert con.execute("SELECT geo_ok FROM vagas").fetchone()[0] is None
