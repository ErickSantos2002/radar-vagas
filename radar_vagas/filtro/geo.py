from __future__ import annotations

import re

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


def elegivel_brasil(geo_raw: str | None, *, confiavel: bool) -> bool | None:
    """True aceita Brasil, False não aceita, None indefinido.

    `confiavel` indica que `geo_raw` é um campo de restrição de contratação
    (Remotive, WWR, Himalayas) e não a localização da empresa (RemoteOK, HN).

    O viés é deixar passar: falso positivo custa um pouco de LLM, falso
    negativo descarta vaga boa em silêncio.
    """
    if not geo_raw or not geo_raw.strip():
        return None
    if _PADRAO.search(geo_raw):
        return True
    return False if confiavel else None
