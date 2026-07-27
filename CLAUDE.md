# radar-vagas

Pipeline que agrega vagas remotas de cinco APIs públicas, filtra elegibilidade
geográfica, pontua contra um perfil configurável e produz um relatório de
tendência de skills.

O design detalhado fica em `docs/specs/`, **fora do git** (ver `.gitignore`).

## ⚠️ Repositório público — regra de push

**Antes de qualquer `git push`, conferir o que está subindo.** Não é opcional e
não depende do `.gitignore` estar certo: o `.gitignore` protege arquivos novos,
mas não desfaz nada já rastreado, nem cobre conteúdo sensível colado dentro de
um arquivo que legitimamente vai para o repo.

```bash
git status --short                 # nada inesperado como novo/modificado?
git diff --cached                  # ler o diff inteiro, não passar o olho
git ls-files | grep -iE 'perfil|curriculo|currículo|\.env|\.db$|/cv|credential|secret|token'
```

O último comando tem que voltar **vazio**.

**Conferir nome de arquivo não basta — ler o conteúdo.** Um documento com nome
inocente pode carregar dado pessoal, nome de empresa ou informação de contexto
que não deve ficar público e indexável.

Nunca vai para o remoto:

- `perfil.yaml` — dados pessoais, histórico profissional, pretensão salarial
- Currículos e cover letters, em qualquer formato
- `vagas.db` e dumps — contêm descrições de vagas de terceiros
- Relatórios gerados — carregam empresa, faixa salarial, às vezes contato
- Specs e notas de trabalho em `docs/specs/` e `docs/notas/`
- Chave, token, `.env`, credencial de qualquer tipo

Se um segredo já foi commitado, **rotacionar o segredo primeiro** e só depois
limpar o histórico. Remover do índice não basta: quem clonou já tem.

## Convenções

- Python 3.11+ em venv local (`.venv/`), fora do git
- Um adaptador por fonte em `fetch/`, todos com a mesma assinatura
- Estágios sem LLM (`filter`, `radar`) não dependem de rede além das APIs
- O estágio `score` usa `claude -p` (assinatura, sem custo de API).
  **Nunca usar a flag `--bare`** — ela força autenticação por `ANTHROPIC_API_KEY`
  e passa a cobrar por token.
- Lotes de 20 vagas por invocação do `claude -p`, para não torrar limite
- Testes contra fixtures em `tests/fixtures/`, nunca contra a rede
