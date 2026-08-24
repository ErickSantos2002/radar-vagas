-- Par vaga/skill normalizado. O extrator já grava minúsculo, mas normalizar
-- aqui torna o modelo independente de mudança no extrator.

select
    vaga_id,
    lower(trim(skill)) as skill

from {{ source('raw', 'skills') }}
where nullif(trim(skill), '') is not null
