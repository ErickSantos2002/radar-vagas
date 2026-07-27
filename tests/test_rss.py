import xml.etree.ElementTree as ET

import pytest

from radar_vagas.fetch.http import FonteIndisponivel
from radar_vagas.fetch.rss import (
    declarar_prefixos_orfaos,
    parse_tolerante,
    sem_ns,
    texto,
    textos,
)

# Prefixos `orfao:` e `media:` usados sem declaração — é a forma que a
# Himalayas publica e que faz o ElementTree abortar.
XML_ORFAO = """<?xml version="1.0"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <orfao:lastBuildDate>hoje</orfao:lastBuildDate>
    <item>
      <title>Data Engineer</title>
      <media:thumb>x</media:thumb>
      <locationRestriction>Brazil</locationRestriction>
      <locationRestriction>Argentina</locationRestriction>
    </item>
  </channel>
</rss>"""


def test_xml_orfao_quebra_o_parser_padrao() -> None:
    with pytest.raises(ET.ParseError):
        ET.fromstring(XML_ORFAO)


def test_declara_todos_os_prefixos_orfaos() -> None:
    corrigido = declarar_prefixos_orfaos(XML_ORFAO)
    assert 'xmlns:orfao="urn:radar-vagas:orfao"' in corrigido
    assert 'xmlns:media="urn:radar-vagas:media"' in corrigido
    ET.fromstring(corrigido)  # não levanta


def test_nao_redeclara_prefixo_ja_declarado() -> None:
    corrigido = declarar_prefixos_orfaos(XML_ORFAO)
    assert corrigido.count("xmlns:content") == 1


def test_parse_tolerante_devolve_raiz() -> None:
    raiz = parse_tolerante(XML_ORFAO, "teste")
    assert raiz.find(".//item") is not None


def test_parse_tolerante_levanta_em_xml_irrecuperavel() -> None:
    with pytest.raises(FonteIndisponivel):
        parse_tolerante("<rss><channel><item></rss>", "teste")


def test_sem_ns() -> None:
    assert sem_ns("{urn:x}companyName") == "companyName"
    assert sem_ns("title") == "title"


def test_texto_e_textos_ignoram_namespace_e_pegam_repetidos() -> None:
    item = parse_tolerante(XML_ORFAO, "teste").find(".//item")
    assert item is not None
    assert texto(item, "title") == "Data Engineer"
    assert texto(item, "inexistente") is None
    assert textos(item, "locationRestriction") == ["Brazil", "Argentina"]
    assert textos(item, "inexistente") == []
