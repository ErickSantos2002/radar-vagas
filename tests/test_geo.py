import pytest

from radar_vagas.filtro.geo import elegivel_brasil


@pytest.mark.parametrize(
    "geo_raw",
    [
        "Worldwide",
        "worldwide",
        "Anywhere in the World",
        "Brazil",
        "Brasil",
        "LATAM",
        "Latin America",
        "Americas, Europe, Israel",
        "South America",
        "Americas, Europe, Asia, Africa, Oceania",
    ],
)
def test_aceita(geo_raw: str) -> None:
    assert elegivel_brasil(geo_raw, confiavel=True) is True


@pytest.mark.parametrize(
    "geo_raw",
    ["USA", "USA, Canada", "United States", "Europe, UK, Germany, France", "Uruguay"],
)
def test_rejeita_quando_campo_e_confiavel(geo_raw: str) -> None:
    assert elegivel_brasil(geo_raw, confiavel=True) is False


@pytest.mark.parametrize("geo_raw", ["Los Angeles, ", "Beowawe, ", "Indiana, "])
def test_indefinido_quando_campo_nao_e_confiavel(geo_raw: str) -> None:
    assert elegivel_brasil(geo_raw, confiavel=False) is None


@pytest.mark.parametrize("geo_raw", [None, "", "   "])
def test_vazio_e_indefinido(geo_raw: str | None) -> None:
    assert elegivel_brasil(geo_raw, confiavel=True) is None


def test_cidade_brasileira_em_campo_nao_confiavel_ainda_aceita() -> None:
    assert elegivel_brasil("São Paulo, Brazil", confiavel=False) is True
