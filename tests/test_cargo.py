import pytest

from radar_vagas.filtro.cargo import plausivel_data_engineer


@pytest.mark.parametrize(
    "titulo",
    [
        "Data Engineer",
        "Senior Data Engineer",
        "Analytics Engineer",
        "ETL Developer",
        "Data Platform Engineer",
        "Data Infrastructure Engineer",
        "DataOps Engineer",
    ],
)
def test_aprova_por_titulo(titulo: str) -> None:
    assert plausivel_data_engineer(titulo, None) is True


@pytest.mark.parametrize(
    "titulo",
    [
        "Engenheiro de Dados SR",
        "Engenheira de Dados Sênior",
        "Engenheiro(a) de Dados Júnior (Data Engineer)",
        "Engenharia de Dados - Pleno",
        "Arquiteto de Dados",
        "11718371 - ENGENHEIRO DE DADOS SÊNIOR",
        "Engenheiro de Dados Sênior | Automações com IA | Azure",
    ],
)
def test_aprova_titulo_em_portugues(titulo: str) -> None:
    assert plausivel_data_engineer(titulo, None) is True


@pytest.mark.parametrize(
    "titulo",
    ["Analista de Marketing", "Engenheiro Civil", "Professor de Fitdance"],
)
def test_reprova_portugues_fora_do_escopo(titulo: str) -> None:
    assert plausivel_data_engineer(titulo, "Trabalhe conosco.") is False


def test_aprova_por_stack_na_descricao() -> None:
    desc = (
        "You will build pipelines with Airflow, model data in dbt "
        "and load into Snowflake."
    )
    assert plausivel_data_engineer("Software Engineer", desc) is True


def test_reprova_com_menos_de_tres_termos() -> None:
    desc = "You will use Airflow occasionally."
    assert plausivel_data_engineer("Software Engineer", desc) is False


def test_termo_repetido_conta_uma_vez() -> None:
    desc = "dbt dbt dbt dbt models"
    assert plausivel_data_engineer("Software Engineer", desc) is False


@pytest.mark.parametrize(
    "titulo",
    [
        "AI Cinematic Video Editor",
        "Product Sales Specialist",
        "Mental Health Counselor",
    ],
)
def test_reprova_ruido_das_fontes(titulo: str) -> None:
    assert plausivel_data_engineer(titulo, "We are hiring a great person.") is False


def test_descricao_none_nao_quebra() -> None:
    assert plausivel_data_engineer("Sales Manager", None) is False
