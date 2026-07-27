from __future__ import annotations

import html
import re

from radar_vagas.fetch.http import FonteIndisponivel, get_json
from radar_vagas.models import VagaBruta

# As threads mensais canônicas são postadas pelo usuário `whoishiring`.
# `search_by_date` devolve em ordem decrescente de data, então a primeira
# entrada compatível é a thread do mês corrente.
BUSCA = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?tags=story,author_whoishiring&hitsPerPage=6"
)
ITEM = "https://hn.algolia.com/api/v1/items/{}"
FONTE = "hn"

_TAG = re.compile(r"<[^>]+>")


def _limpar(texto: str) -> str:
    return html.unescape(_TAG.sub("\n", texto)).strip()


def escolher_thread(hits: list[dict]) -> dict | None:
    """Escolhe a thread 'Who is hiring?' mais recente.

    O `whoishiring` posta três threads por mês; só interessa a de contratação,
    não a 'Who wants to be hired?' nem a de freelance.
    """
    for h in hits:
        titulo = (h.get("title") or "").lower()
        if "who is hiring" in titulo and "wants to be hired" not in titulo:
            return h
    return None


def parse_hn(item: dict) -> list[VagaBruta]:
    """Cada comentário de primeiro nível é um anúncio em texto livre.

    Não há campo de elegibilidade, então `geo_confiavel=False` e o filtro de
    cargo faz o trabalho pesado.
    """
    vagas: list[VagaBruta] = []
    for c in item.get("children") or []:
        texto = c.get("text")
        ident = c.get("id")
        if ident is None or not texto or not texto.strip():
            continue
        limpo = _limpar(texto)
        if not limpo:
            continue
        primeira = limpo.splitlines()[0].strip()
        if not primeira:
            continue
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=str(ident),
                url=f"https://news.ycombinator.com/item?id={ident}",
                titulo=primeira[:200],
                empresa=None,
                geo_raw=None,
                geo_confiavel=False,
                publicado_em=c.get("created_at"),
                descricao=limpo,
                salario_raw=None,
            )
        )
    return vagas


def buscar_hn() -> list[VagaBruta]:
    busca = get_json(BUSCA)
    if not isinstance(busca, dict) or not busca.get("hits"):
        raise FonteIndisponivel("hn: busca não retornou threads")
    thread = escolher_thread(busca["hits"])
    if thread is None:
        raise FonteIndisponivel("hn: nenhuma thread 'Who is hiring?' nos resultados")
    item = get_json(ITEM.format(thread["objectID"]))
    if not isinstance(item, dict):
        raise FonteIndisponivel("hn: item não é objeto")
    return parse_hn(item)
