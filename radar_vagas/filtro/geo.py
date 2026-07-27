from __future__ import annotations

import re
import unicodedata

_ACEITA = (
    "worldwide",
    "anywhere",
    "global",
    "brazil",
    "brasil",
    "latam",
    "latin america",
    "south america",
    "americas",
)

_PADRAO = re.compile("|".join(re.escape(t) for t in _ACEITA), re.IGNORECASE)


def _sem_acento(texto: str) -> str:
    """'Latin América' -> 'Latin America'.

    As fontes escrevem região em português e espanhol também; sem normalizar,
    'Latin América' e 'Brasília' não casariam com os padrões ASCII.
    """
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def elegivel_brasil(geo_raw: str | None, *, confiavel: bool) -> bool | None:
    """True aceita Brasil, False não aceita, None indefinido.

    `confiavel` indica que `geo_raw` é um campo de restrição de contratação
    (Remotive, WWR, Himalayas) e não a localização da empresa (RemoteOK, HN).

    O viés é deixar passar: falso positivo custa um pouco de LLM, falso
    negativo descarta vaga boa em silêncio.
    """
    if not geo_raw or not geo_raw.strip():
        return None
    if _PADRAO.search(_sem_acento(geo_raw)):
        return True
    return False if confiavel else None


def sinal_no_titulo(titulo: str) -> bool:
    """True se o título sugere elegibilidade mais ampla que o campo estruturado.

    Existe porque a Himalayas publica restrição mais estreita que o anúncio: uma
    vaga intitulada 'Data Engineer — Remote, Latin América' vinha com
    `locationRestriction = Costa Rica`. Quando título e campo se contradizem, o
    resultado passa a ser indefinido e o scoring decide, em vez de descartar.
    """
    return bool(_PADRAO.search(_sem_acento(titulo or "")))
