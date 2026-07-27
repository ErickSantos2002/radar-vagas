from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from radar_vagas.fetch.http import FonteIndisponivel

_PREFIXO_USADO = re.compile(r"</?([A-Za-z][\w.-]*):")
_RAIZ = re.compile(r"<(?:[\w.-]+:)?(?:rss|feed)\b[^>]*>")
_NAMESPACE = re.compile(r"\{[^}]*\}")


def declarar_prefixos_orfaos(xml: str) -> str:
    """Declara no elemento raiz qualquer prefixo usado mas não declarado.

    O RSS da Himalayas usa `himalayasJobs:` e `media:` sem declarar o namespace,
    o que faz o ElementTree abortar com "unbound prefix". Em vez de assumir
    quais prefixos faltam, detecta e declara todos os órfãos.
    """
    m = _RAIZ.search(xml)
    if m is None:
        return xml
    raiz = m.group(0)
    usados = set(_PREFIXO_USADO.findall(xml))
    declarados = set(re.findall(r"xmlns:([\w.-]+)", raiz))
    faltando = usados - declarados - {"xml"}
    if not faltando:
        return xml
    extra = "".join(f' xmlns:{p}="urn:radar-vagas:{p}"' for p in sorted(faltando))
    return xml.replace(raiz, raiz[:-1] + extra + ">", 1)


def parse_tolerante(xml: str, fonte: str) -> ET.Element:
    """Parseia RSS/Atom, tolerando prefixo de namespace não declarado."""
    try:
        return ET.fromstring(declarar_prefixos_orfaos(xml))
    except ET.ParseError as exc:
        raise FonteIndisponivel(f"{fonte}: XML inválido — {exc}") from exc


def sem_ns(tag: str) -> str:
    """`{urn:x}companyName` -> `companyName`."""
    return _NAMESPACE.sub("", tag)


def texto(item: ET.Element, nome: str) -> str | None:
    """Primeiro filho cujo nome local é `nome`, ignorando namespace."""
    for filho in item:
        if sem_ns(filho.tag) == nome and filho.text and filho.text.strip():
            return filho.text.strip()
    return None


def textos(item: ET.Element, nome: str) -> list[str]:
    """Todos os filhos cujo nome local é `nome` (tags repetidas)."""
    return [
        filho.text.strip()
        for filho in item
        if sem_ns(filho.tag) == nome and filho.text and filho.text.strip()
    ]
