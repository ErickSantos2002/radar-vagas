from collections import Counter

from radar_vagas.relatorio import Vaga, gerar_markdown, nome_arquivo, semana_iso


def _vaga(**kw) -> Vaga:
    base: dict[str, object] = {
        "fonte": "remotive",
        "empresa": "Acme",
        "titulo": "Data Engineer",
        "geo_raw": "Worldwide",
        "geo_ok": 1,
        "url": "https://acme.test/vaga",
        "skills": ["dbt", "airflow"],
    }
    base.update(kw)
    return Vaga(**base)  # type: ignore[arg-type]


def test_semana_iso_e_nome_do_arquivo() -> None:
    assert semana_iso("2026-07-27T10:00:00+00:00") == "2026-W31"
    assert nome_arquivo("2026-W31") == "Semana-2026-W31.md"


def test_comeca_com_titulo_e_sem_frontmatter() -> None:
    md = gerar_markdown("2026-W31", [_vaga()], Counter({"dbt": 1}), 100)
    assert not md.startswith("---"), "vault não usa frontmatter YAML"
    assert md.startswith("# Radar de Vagas — Semana 2026-W31")


def test_termina_com_notas_relacionadas_linkando_a_meta() -> None:
    md = gerar_markdown("2026-W31", [_vaga()], Counter({"dbt": 1}), 100)
    assert "## Notas relacionadas" in md
    assert "[[../Trabalho-Remoto|Trabalho Remoto]]" in md
    # a seção é a última coisa da nota, e é uma lista de links
    corpo, _, notas = md.rpartition("## Notas relacionadas")
    assert corpo, "seção de notas relacionadas deve vir depois do conteúdo"
    linhas = [ln for ln in notas.splitlines() if ln.strip()]
    assert linhas and all(ln.startswith("- [[") for ln in linhas)


def test_lista_a_vaga_com_link_e_regiao() -> None:
    md = gerar_markdown("2026-W31", [_vaga()], Counter({"dbt": 1}), 100)
    assert "Acme" in md
    assert "Data Engineer" in md
    assert "https://acme.test/vaga" in md
    assert "Worldwide" in md


def test_marca_elegibilidade_indefinida() -> None:
    md = gerar_markdown(
        "2026-W31", [_vaga(geo_ok=None, geo_raw="Costa Rica")], Counter(), 100
    )
    assert "a confirmar" in md.lower()


def test_ranking_de_skills_ordenado_com_percentual() -> None:
    md = gerar_markdown(
        "2026-W31",
        [_vaga(), _vaga(empresa="Beta")],
        Counter({"dbt": 2, "airflow": 1}),
        100,
    )
    # medir a ordem dentro da seção de ranking, não na listagem das vagas
    ranking = md.split("## O que o mercado está pedindo", 1)[1]
    ranking = ranking.split("## Notas relacionadas", 1)[0]
    assert ranking.index("`dbt`") < ranking.index("`airflow`")
    assert "100%" in ranking  # dbt em 2 de 2 vagas
    assert "50%" in ranking  # airflow em 1 de 2


def test_sem_vagas_ainda_gera_nota_util() -> None:
    md = gerar_markdown("2026-W31", [], Counter(), 250)
    assert md.startswith("# Radar de Vagas")
    assert "250" in md
    assert "## Notas relacionadas" in md
