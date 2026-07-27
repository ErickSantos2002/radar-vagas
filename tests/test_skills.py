from radar_vagas.db import conectar, criar_schema, inserir_vagas
from radar_vagas.models import VagaBruta
from radar_vagas.skills import contar_skills, extrair_skills, gravar_skills


def test_extrai_e_canoniza() -> None:
    desc = "We use Apache Airflow, DBT, snowflake and Postgres."
    assert extrair_skills(desc) == {"airflow", "dbt", "snowflake", "postgresql"}


def test_aliases_convergem_para_o_mesmo_canonico() -> None:
    assert extrair_skills("Apache Airflow") == extrair_skills("airflow")
    assert extrair_skills("PostgreSQL") == extrair_skills("Postgres")
    assert extrair_skills("GCP") == extrair_skills("Google Cloud Platform")


def test_nao_casa_dentro_de_palavra() -> None:
    # 'r' como linguagem não pode casar dentro de qualquer palavra,
    # e 'go' não pode casar em 'going'
    assert extrair_skills("We are going to hire") == set()
    assert extrair_skills("Experience with R and Go") == {"r", "go"}


def test_descricao_vazia() -> None:
    assert extrair_skills(None) == set()
    assert extrair_skills("") == set()


def test_grava_e_conta() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    vagas = [
        VagaBruta(
            fonte="t",
            external_id=str(i),
            url="https://t.test",
            titulo="Data Engineer",
            empresa="Acme",
            geo_raw="Worldwide",
            geo_confiavel=True,
            publicado_em=None,
            descricao=desc,
            salario_raw=None,
        )
        for i, desc in enumerate(["dbt and airflow", "dbt only", "spark and kafka"])
    ]
    inserir_vagas(con, vagas, {v.external_id: True for v in vagas})
    gravar_skills(con, vagas)

    contagem = contar_skills(con)
    assert contagem["dbt"] == 2
    assert contagem["airflow"] == 1
    assert contagem["spark"] == 1
    assert contagem["kafka"] == 1


def test_gravar_skills_e_idempotente() -> None:
    con = conectar(":memory:")
    criar_schema(con)
    v = VagaBruta(
        fonte="t",
        external_id="1",
        url="https://t.test",
        titulo="Data Engineer",
        empresa=None,
        geo_raw="Worldwide",
        geo_confiavel=True,
        publicado_em=None,
        descricao="dbt airflow",
        salario_raw=None,
    )
    inserir_vagas(con, [v], {"1": True})
    gravar_skills(con, [v])
    gravar_skills(con, [v])
    assert con.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 2
