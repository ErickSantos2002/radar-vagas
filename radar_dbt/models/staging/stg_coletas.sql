-- Uma linha por execução do coletor. As vagas reprovadas no filtro não são
-- gravadas, então esta é a única tabela que sabe quantas foram vistas.

select
    id                as coleta_id,
    quando::timestamptz as executada_em,
    coletadas,
    aprovadas,
    novas,
    round(100.0 * aprovadas / nullif(coletadas, 0), 1) as pct_aprovacao,
    round(100.0 * novas     / nullif(aprovadas, 0), 1) as pct_ineditas

from {{ source('raw', 'runs') }}
