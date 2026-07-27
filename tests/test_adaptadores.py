import json
from pathlib import Path

from radar_vagas.fetch.himalayas import parse_himalayas
from radar_vagas.fetch.hn import escolher_thread, parse_hn
from radar_vagas.fetch.remoteok import parse_remoteok
from radar_vagas.fetch.remotive import parse_remotive
from radar_vagas.fetch.wwr import _separar, parse_wwr

FIXTURES = Path(__file__).parent / "fixtures"


def _ler(nome: str):
    return json.loads((FIXTURES / nome).read_text())


# ─────────────────────────── Remotive ───────────────────────────


def test_remotive_normaliza() -> None:
    vagas = parse_remotive(_ler("remotive.json"))
    assert vagas, "fixture da Remotive veio vazia"
    v = vagas[0]
    assert v.fonte == "remotive"
    assert v.external_id and isinstance(v.external_id, str)
    assert v.url.startswith("http")
    assert v.titulo
    assert v.geo_confiavel is True


def test_remotive_ids_unicos() -> None:
    ids = [v.external_id for v in parse_remotive(_ler("remotive.json"))]
    assert len(ids) == len(set(ids))


# ─────────────────────────── RemoteOK ───────────────────────────


def test_remoteok_descarta_metadata() -> None:
    payload = _ler("remoteok.json")
    assert "legal" in payload[0], "fixture mudou: primeiro item não é mais metadata"
    vagas = parse_remoteok(payload)
    assert vagas
    assert all(v.titulo for v in vagas)
    assert len(vagas) <= len(payload) - 1


def test_remoteok_geo_nao_confiavel() -> None:
    vagas = parse_remoteok(_ler("remoteok.json"))
    assert vagas
    assert all(v.geo_confiavel is False for v in vagas)
    assert all(v.fonte == "remoteok" for v in vagas)


# ──────────────────────── We Work Remotely ──────────────────────


def test_wwr_normaliza() -> None:
    vagas = parse_wwr((FIXTURES / "wwr.xml").read_text())
    assert vagas
    v = vagas[0]
    assert v.fonte == "wwr"
    assert v.geo_confiavel is True
    assert v.url.startswith("http")


def test_wwr_separa_empresa_do_titulo() -> None:
    assert _separar("JetBrains: Backend Engineer") == ("JetBrains", "Backend Engineer")
    assert _separar("Backend Engineer") == (None, "Backend Engineer")


# ─────────────────────────── Himalayas ──────────────────────────


def test_himalayas_normaliza() -> None:
    vagas = parse_himalayas(_ler("himalayas.json"))
    assert vagas
    v = vagas[0]
    assert v.fonte == "himalayas"
    assert v.geo_confiavel is True
    assert v.external_id.startswith("http")


def test_himalayas_junta_lista_de_restricoes() -> None:
    payload = {
        "jobs": [
            {
                "guid": "https://himalayas.app/x",
                "title": "Data Engineer",
                "companyName": "Acme",
                "locationRestrictions": ["Brazil", "Argentina"],
                "pubDate": 1785158945,
                "description": "d",
            }
        ]
    }
    assert parse_himalayas(payload)[0].geo_raw == "Brazil, Argentina"


def test_himalayas_pubdate_epoch_vira_iso_e_lista_vazia_vira_none() -> None:
    payload = {
        "jobs": [
            {
                "guid": "https://himalayas.app/y",
                "title": "Data Engineer",
                "companyName": "Acme",
                "locationRestrictions": [],
                "pubDate": 1785158945,
                "description": "d",
            }
        ]
    }
    v = parse_himalayas(payload)[0]
    assert v.publicado_em is not None
    assert v.publicado_em.startswith("2026-")
    assert v.geo_raw is None


# ────────────────────────────── HN ──────────────────────────────


def test_hn_usa_primeira_linha_como_titulo() -> None:
    item = {
        "children": [
            {
                "id": 111,
                "text": "Acme | Data Engineer | REMOTE (worldwide)<p>We use dbt and Airflow.",
                "created_at": "2026-07-01T12:00:00.000Z",
            }
        ]
    }
    v = parse_hn(item)[0]
    assert v.external_id == "111"
    assert v.titulo == "Acme | Data Engineer | REMOTE (worldwide)"
    assert v.url == "https://news.ycombinator.com/item?id=111"
    assert v.geo_confiavel is False


def test_hn_ignora_comentario_vazio_ou_removido() -> None:
    item = {"children": [{"id": 1, "text": None}, {"id": 2, "text": "   "}, {"id": 3}]}
    assert parse_hn(item) == []


def test_hn_fixture_real_produz_vagas() -> None:
    vagas = parse_hn(_ler("hn_item.json"))
    assert vagas, "fixture do HN veio sem comentários"
    assert all(v.fonte == "hn" for v in vagas)
    assert all(v.titulo for v in vagas)


def test_hn_escolhe_who_is_hiring_e_nao_who_wants_to_be_hired() -> None:
    hits = _ler("hn_story.json")["hits"]
    escolhido = escolher_thread(hits)
    assert escolhido is not None
    assert "who is hiring" in escolhido["title"].lower()
    assert "wants to be hired" not in escolhido["title"].lower()


def test_hn_escolhe_a_mais_recente() -> None:
    hits = [
        {"objectID": "2", "title": "Ask HN: Who is hiring? (June 2026)"},
        {"objectID": "1", "title": "Ask HN: Who is hiring? (July 2026)"},
    ]
    # search_by_date já vem ordenado desc, então o primeiro compatível ganha
    assert escolher_thread(hits)["objectID"] == "2"


def test_hn_sem_thread_compativel_devolve_none() -> None:
    assert escolher_thread([{"objectID": "9", "title": "Ask HN: Who wants to be hired?"}]) is None
