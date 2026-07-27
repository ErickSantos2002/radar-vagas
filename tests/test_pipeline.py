from radar_vagas.filtro import aplicar_filtros
from radar_vagas.models import VagaBruta


def _v(
    *,
    fonte: str = "t",
    external_id: str = "1",
    url: str = "https://t.test",
    titulo: str = "Data Engineer",
    empresa: str | None = None,
    geo_raw: str | None = "Worldwide",
    geo_confiavel: bool = True,
    publicado_em: str | None = None,
    descricao: str | None = "dbt airflow snowflake",
    salario_raw: str | None = None,
) -> VagaBruta:
    return VagaBruta(
        fonte=fonte,
        external_id=external_id,
        url=url,
        titulo=titulo,
        empresa=empresa,
        geo_raw=geo_raw,
        geo_confiavel=geo_confiavel,
        publicado_em=publicado_em,
        descricao=descricao,
        salario_raw=salario_raw,
    )


def test_mantem_vaga_elegivel_e_plausivel() -> None:
    aprovadas, geo = aplicar_filtros([_v()])
    assert len(aprovadas) == 1
    assert geo["1"] is True


def test_descarta_geo_negativo() -> None:
    aprovadas, _ = aplicar_filtros([_v(geo_raw="USA", geo_confiavel=True)])
    assert aprovadas == []


def test_mantem_geo_indefinido() -> None:
    aprovadas, geo = aplicar_filtros(
        [_v(geo_raw="Los Angeles, ", geo_confiavel=False)]
    )
    assert len(aprovadas) == 1
    assert geo["1"] is None


def test_titulo_amplo_sobrepoe_campo_estruturado_estreito() -> None:
    # Caso real da Himalayas: locationRestriction='Costa Rica' num anúncio
    # intitulado "Remote, Latin América". Não pode ser descartado.
    aprovadas, geo = aplicar_filtros(
        [
            _v(
                titulo="Data Engineer (Senior) - ETL - Remote, Latin América",
                geo_raw="Costa Rica",
                geo_confiavel=True,
            )
        ]
    )
    assert len(aprovadas) == 1
    assert geo["1"] is None


def test_titulo_sem_regiao_nao_resgata_geo_negativo() -> None:
    aprovadas, _ = aplicar_filtros(
        [_v(titulo="Data Engineer", geo_raw="United States", geo_confiavel=True)]
    )
    assert aprovadas == []


def test_descarta_cargo_implausivel() -> None:
    aprovadas, _ = aplicar_filtros(
        [_v(titulo="Product Sales Specialist", descricao="Sell things.")]
    )
    assert aprovadas == []
