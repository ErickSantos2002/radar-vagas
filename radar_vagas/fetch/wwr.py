from __future__ import annotations

import xml.etree.ElementTree as ET

from radar_vagas.fetch.http import FonteIndisponivel, get_text
from radar_vagas.models import VagaBruta

URLS = (
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
)
FONTE = "wwr"


def _separar(titulo: str) -> tuple[str | None, str]:
    """WWR entrega 'Empresa: Cargo'. Devolve (empresa, cargo)."""
    if ": " in titulo:
        empresa, _, cargo = titulo.partition(": ")
        return empresa.strip(), cargo.strip()
    return None, titulo.strip()


def _texto(item: ET.Element, tag: str) -> str | None:
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else None


def parse_wwr(xml_texto: str) -> list[VagaBruta]:
    try:
        raiz = ET.fromstring(xml_texto)
    except ET.ParseError as exc:
        raise FonteIndisponivel(f"wwr: XML inválido — {exc}") from exc

    vagas: list[VagaBruta] = []
    for item in raiz.iterfind(".//item"):
        bruto = _texto(item, "title")
        link = _texto(item, "link")
        guid = _texto(item, "guid") or link
        if not bruto or not link or not guid:
            continue
        empresa, cargo = _separar(bruto)
        vagas.append(
            VagaBruta(
                fonte=FONTE,
                external_id=guid,
                url=link,
                titulo=cargo,
                empresa=empresa,
                geo_raw=_texto(item, "region"),
                geo_confiavel=True,
                publicado_em=_texto(item, "pubDate"),
                descricao=_texto(item, "description"),
                salario_raw=None,
            )
        )
    return vagas


def buscar_wwr() -> list[VagaBruta]:
    """Coleta as categorias configuradas, deduplicando entre elas.

    A mesma vaga pode aparecer em duas categorias do RSS; sem o dedupe local
    o `inserir_vagas` receberia duplicata dentro do mesmo lote.
    """
    vagas: list[VagaBruta] = []
    vistos: set[str] = set()
    for url in URLS:
        for v in parse_wwr(get_text(url)):
            if v.external_id not in vistos:
                vistos.add(v.external_id)
                vagas.append(v)
    return vagas
