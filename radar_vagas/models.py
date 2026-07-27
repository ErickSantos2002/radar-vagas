from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VagaBruta:
    """Uma vaga já normalizada por um adaptador, antes de qualquer filtro."""

    fonte: str
    external_id: str
    url: str
    titulo: str
    empresa: str | None
    geo_raw: str | None
    geo_confiavel: bool
    publicado_em: str | None  # ISO 8601
    descricao: str | None
    salario_raw: str | None
