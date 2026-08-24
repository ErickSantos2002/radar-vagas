-- Uma linha por vaga, com tipo de verdade em vez de texto.
-- O SQLite guarda tudo como texto e booleano como 0/1; aqui isso vira
-- timestamp e boolean, para o resto do projeto não repetir cast.

with bruto as (

    select * from {{ source('raw', 'vagas') }}

)

select
    id                                as vaga_id,
    fonte,
    external_id,
    url,
    nullif(trim(titulo), '')          as titulo,
    nullif(trim(empresa), '')         as empresa,
    geo_raw,

    -- geo_ok nulo significa "não deu para confirmar", não "reprovado".
    -- Manter os dois casos separados evita contar palpite como certeza.
    geo_ok = 1                        as geo_confiavel,
    geo_ok is null                    as geo_indefinido,

    -- Fonte externa: nem toda data vem em ISO. O que não casar vira nulo em
    -- vez de derrubar o modelo inteiro.
    case
        when publicado_em ~ '^\d{4}-\d{2}-\d{2}'
        then publicado_em::timestamptz
    end                               as publicado_em,

    visto_em::timestamptz             as visto_em,
    status,
    tentativas,
    coalesce(length(descricao), 0) > 0 as tem_descricao

from bruto
