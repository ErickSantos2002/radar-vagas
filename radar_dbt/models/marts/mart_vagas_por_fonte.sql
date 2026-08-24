-- Rendimento de cada fonte depois do filtro. Fonte que coleta muito e aprova
-- nada é candidata a sair do radar: custa requisição e não entrega vaga.

select
    fonte,
    count(*)                                          as vagas,
    count(*) filter (where geo_confiavel)             as geo_confirmadas,
    count(*) filter (where geo_indefinido)            as geo_indefinidas,
    count(*) filter (where tem_descricao)             as com_descricao,
    count(distinct empresa)                           as empresas,
    min(publicado_em)                                 as vaga_mais_antiga,
    max(publicado_em)                                 as vaga_mais_recente,
    max(visto_em)                                     as ultima_coleta

from {{ ref('stg_vagas') }}
group by fonte
order by vagas desc
