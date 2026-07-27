import pytest

from radar_vagas.filtro.presencial import e_presencial


@pytest.mark.parametrize(
    "titulo",
    [
        "DoubleVerify | Sr. Data Engineer I | ONSITE/HYBRID - New York, NY (3x/week)",
        "Connie Health | Senior Analytics Engineer | Boston, MA | HYBRID | $150k",
        "Data Engineer | On-site | Berlin",
        "89k for sr data engineer in nyc onsite? thats really depressing",
        "Engenheiro de Dados — Presencial São Paulo",
        "Engenheiro de Dados (Híbrido 3x na semana)",
        "Data Engineer - In Office",
    ],
)
def test_detecta_presencial_e_hibrido(titulo: str) -> None:
    assert e_presencial(titulo) is True


@pytest.mark.parametrize(
    "titulo",
    [
        "IPinfo.io | Data Engineer | REMOTE (Anywhere) | Full-time",
        "Engenheiro de Dados SR",
        "Senior Software Engineer - Data Platform",
        "Data Engineer | REMOTE | Full-time",
        "Analytics Engineer, LATAM",
        "",
    ],
)
def test_nao_marca_remoto_como_presencial(titulo: str) -> None:
    assert e_presencial(titulo) is False


def test_remote_first_nao_e_falso_positivo() -> None:
    # "remote-first, never hybrid" nao pode ser lido como hibrido
    assert e_presencial("Data Engineer — remote-first company") is False


def test_hibrido_sem_acento() -> None:
    assert e_presencial("Engenheiro de Dados - Hibrido") is True
