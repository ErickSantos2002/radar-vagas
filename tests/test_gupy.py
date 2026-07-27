import json
from pathlib import Path

from radar_vagas.fetch.gupy import parse_gupy
from radar_vagas.filtro.cargo import plausivel_data_engineer
from radar_vagas.filtro.geo import elegivel_brasil

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture() -> dict:
    return json.loads((FIXTURES / "gupy.json").read_text())


def test_normaliza() -> None:
    vagas = parse_gupy(_fixture())
    assert vagas
    v = vagas[0]
    assert v.fonte == "gupy"
    assert v.external_id and isinstance(v.external_id, str)
    assert v.url.startswith("http")
    assert v.titulo
    assert v.empresa


def test_so_aceita_workplace_remote() -> None:
    payload = {
        "data": [
            {"id": 1, "name": "Engenheiro de Dados", "jobUrl": "https://a.test",
             "careerPageName": "A", "workplaceType": "remote", "country": "Brasil"},
            {"id": 2, "name": "Engenheiro de Dados", "jobUrl": "https://b.test",
             "careerPageName": "B", "workplaceType": "hybrid", "country": "Brasil"},
            {"id": 3, "name": "Engenheiro de Dados", "jobUrl": "https://c.test",
             "careerPageName": "C", "workplaceType": "on-site", "country": "Brasil"},
        ]
    }
    vagas = parse_gupy(payload)
    assert [v.external_id for v in vagas] == ["1"]


def test_geo_e_confiavel_e_aceita_brasil() -> None:
    vagas = parse_gupy(_fixture())
    v = vagas[0]
    assert v.geo_confiavel is True
    assert elegivel_brasil(v.geo_raw, confiavel=v.geo_confiavel) is True


def test_vagas_da_fixture_passam_no_filtro_de_cargo() -> None:
    # Sem os padrões em português, "Engenheiro de Dados" seria descartado.
    vagas = parse_gupy(_fixture())
    aprovadas = [v for v in vagas if plausivel_data_engineer(v.titulo, v.descricao)]
    assert len(aprovadas) >= len(vagas) * 0.8, (
        f"só {len(aprovadas)} de {len(vagas)} passaram — filtro de cargo "
        "não está reconhecendo os títulos em português"
    )


def test_ids_unicos() -> None:
    ids = [v.external_id for v in parse_gupy(_fixture())]
    assert len(ids) == len(set(ids))
