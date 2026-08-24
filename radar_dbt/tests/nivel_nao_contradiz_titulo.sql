-- Um título que diz "Júnior" nunca pode sair classificado como sênior.
-- Se este teste falhar, a régua de senioridade quebrou.
select vaga_id, titulo, nivel
from {{ ref('int_vagas_nivel') }}
where titulo ~* '(j[uú]nior|\mjr\M)'
  and nivel in ('senior', 'pleno')
