from __future__ import annotations

from radar_vagas.fetch.http import get_text
from radar_vagas.fetch.rss import parse_tolerante, texto, textos
from radar_vagas.models import VagaBruta

# A API pública (`/jobs/api`) devolve no máximo 20 vagas por chamada, ignora
# `limit` e não aceita nenhum filtro de categoria — com `totalCount` em ~96 mil,
# achar vagas de dados por ali exigiria milhares de requisições. O RSS geral
# devolve ~100 itens numa chamada, então é a fonte melhor apesar de não trazer
# faixa salarial (o scoring extrai da descrição na Fase 4).
URL = "https://himalayas.app/jobs/rss"
FONTE = "himalayas"


def parse_himalayas(xml_texto: str) -> list[VagaBruta]:
    raiz = parse_tolerante(xml_texto, FONTE)
    vagas: list[VagaBruta] = []
    for item in raiz.iterfind(".//item"):
        titulo = texto(item, "title")
        guid = texto(item, "guid") or texto(item, "link")
        link = texto(item, "link") or guid
        if not titulo or not guid or not link:
            continue
        restricoes = textos(item, "locationRestriction")
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=guid,
                url=link,
                titulo=titulo,
                empresa=texto(item, "companyName"),
                geo_raw=", ".join(restricoes) if restricoes else None,
                geo_confiavel=True,
                publicado_em=texto(item, "pubDate"),
                descricao=texto(item, "encoded") or texto(item, "description"),
                salario_raw=None,
            )
        )
    return vagas


def buscar_himalayas() -> list[VagaBruta]:
    return parse_himalayas(get_text(URL))
