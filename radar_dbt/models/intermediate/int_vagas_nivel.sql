-- Classificação de senioridade da vaga.
--
-- Por que não basta o título: a Viacerta anunciou "Engenheiro de Dados" e só
-- na primeira linha da descrição disse "Júnior". Classificar por título perde
-- vaga elegível, que é o erro caro aqui — descartar uma vaga boa custa mais
-- que olhar uma ruim.
--
-- A ordem de precedência é deliberada e a coluna `motivo` registra qual regra
-- decidiu, para a classificação poder ser auditada em vez de confiada.

with base as (

    select
        v.*,
        -- O nível declarado costuma estar na abertura ("estamos em busca de
        -- um(a) X Júnior"), não no meio do texto de responsabilidades.
        left(coalesce(d.descricao, ''), 300) as abertura,
        d.descricao                          as descricao_completa
    from {{ ref('stg_vagas') }} v
    left join {{ source('raw', 'vagas') }} d on d.id = v.vaga_id

), sinais as (

    select
        *,

        case
            when titulo ~* '(est[aá]gi|\mintern\M|trainee|aprendiz)'          then 'estagio'
            -- Sênior é testado antes de pleno de propósito: "Eng de Dados
            -- Pl/Sr" exige sênior, e classificar para baixo criaria falsa
            -- esperança.
            when titulo ~* '(s[êe]nior|\msr\M|especialista|specialist|lead|principal|staff|arquiteto|coordenador|gerente|manager|head|l[ií]der)' then 'senior'
            when titulo ~* '(j[uú]nior|\mjr\M)'                              then 'junior'
            when titulo ~* '(pleno|\mpl\M)'                                  then 'pleno'
        end as nivel_titulo,

        -- O nível só conta se estiver colado no cargo. Sem isso, "reunimos
        -- mais de 500 especialistas" na apresentação da empresa classificava
        -- a vaga como sênior (aconteceu, com a WEBJUMP).
        case
            when abertura ~* '{{ var("cargo_regex") }}[^.]{0,60}(j[uú]nior|\mjr\M)'   then 'junior'
            when abertura ~* '{{ var("cargo_regex") }}[^.]{0,60}pleno'                 then 'pleno'
            when abertura ~* '{{ var("cargo_regex") }}[^.]{0,60}(s[êe]nior|especialista)' then 'senior'
        end as nivel_abertura,

        -- "5 anos de experiência" é o sinal mais honesto quando não há rótulo.
        nullif(substring(descricao_completa from '(?i)([0-9]+)\s*\+?\s*anos? de experi'), '')::int as anos_exigidos,

        -- Só conta mentoria que a vaga EXIGE. "Programas de mentoria com
        -- líderes" é benefício oferecido ao contratado e classificava a vaga
        -- como sênior (aconteceu, com a BIP Brasil).
        descricao_completa ~* '(atuar como mentor|ser mentor|mentorar|mentoria t[eé]cnica|membros mais j[uú]niores|profissionais mais j[uú]niores)' as pede_mentoria

    from base

)

select
    vaga_id,
    fonte,
    empresa,
    titulo,
    url,
    visto_em,
    nivel_titulo,
    nivel_abertura,
    anos_exigidos,
    pede_mentoria,

    coalesce(
        nivel_titulo,
        nivel_abertura,
        case
            when pede_mentoria             then 'senior'
            when anos_exigidos >= 5        then 'senior'
            when anos_exigidos between 3 and 4 then 'pleno'
            when anos_exigidos <= 2        then 'junior'
        end,
        'indefinido'
    ) as nivel,

    case
        when nivel_titulo   is not null then 'titulo'
        when nivel_abertura is not null then 'abertura da descricao'
        when pede_mentoria              then 'pede mentoria de juniores'
        when anos_exigidos  is not null then anos_exigidos || ' anos exigidos'
        else 'nao declarado'
    end as motivo

from sinais
