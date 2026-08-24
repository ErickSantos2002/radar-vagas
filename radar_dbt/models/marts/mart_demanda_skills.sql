-- Quanto cada skill aparece nas vagas que sobreviveram ao filtro.
-- É a tabela que responde a pergunta que originou o projeto: o que estudar
-- primeiro para as vagas que eu de fato posso pegar.

with vagas as (

    select * from {{ ref('stg_vagas') }}

), skills as (

    select * from {{ ref('stg_skills') }}

), total as (

    select count(*) as vagas_no_periodo from vagas

)

select
    s.skill,
    count(distinct s.vaga_id)                                      as vagas,
    round(100.0 * count(distinct s.vaga_id)
          / nullif((select vagas_no_periodo from total), 0), 1)    as pct_das_vagas,

    -- Gupy é a única fonte brasileira do radar; separar mostra se a skill é
    -- exigida aqui ou só no mercado de fora, que paga em dólar e raramente
    -- contrata júnior no Brasil.
    count(distinct case when v.fonte = 'gupy' then s.vaga_id end)  as vagas_br,
    count(distinct case when v.fonte <> 'gupy' then s.vaga_id end) as vagas_exterior

from skills s
join vagas v on v.vaga_id = s.vaga_id
group by s.skill
order by vagas desc
