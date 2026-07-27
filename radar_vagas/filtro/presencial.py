from __future__ import annotations

import re

from radar_vagas.filtro.geo import _sem_acento

# Marcadores fortes de trabalho presencial ou híbrido. Aplicados ao TÍTULO, não
# à descrição: é no título que os boards e o HN declaram a modalidade
# ("| ONSITE/HYBRID - New York, NY |"), e a descrição produz falso positivo
# fácil ("we are remote-first, never hybrid").
_MARCADORES = (
    r"on-?\s?site",
    r"hybrid",
    r"hibrido",
    r"presencial",
    r"in[-\s]office",
    r"semi-?presencial",
)

_PADRAO = re.compile("|".join(_MARCADORES), re.IGNORECASE)

# "remote-first" e afins podem conter as palavras acima numa negação.
_NEGACAO = re.compile(r"n(o|ever|ão|ao)\s+(hybrid|hibrido|presencial|on-?site)", re.I)


def e_presencial(titulo: str) -> bool:
    """True se o título indica trabalho presencial ou híbrido.

    O Erick não quer nada que exija presença. Para o Gupy isso já vem resolvido
    pelo `workplaceType=remote` da API; este filtro cobre as fontes que só
    declaram a modalidade em texto livre — HN acima de tudo.
    """
    if not titulo:
        return False
    limpo = _sem_acento(titulo)
    if _NEGACAO.search(limpo):
        return False
    return bool(_PADRAO.search(limpo))
