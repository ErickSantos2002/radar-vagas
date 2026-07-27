# radar-vagas

Pipeline de dados que agrega vagas remotas de cinco fontes públicas, resolve
elegibilidade geográfica, extrai skills exigidas com LLM e produz um relatório
de tendência do mercado.

> 🚧 Em construção. Fase 1 de 7 — ver [Roadmap](#roadmap).

## O problema

O mercado de trabalho remoto é fragmentado entre dezenas de boards, cada um com
seu próprio schema, e a informação mais importante — **quem essa vaga pode
contratar** — é a menos padronizada de todas. O mesmo campo aparece como
`"Worldwide"`, `"Americas, Europe, Israel"`, `"USA, CST (UTC-6)"` ou
simplesmente ausente, e boa parte das vagas anunciadas como "remote" na verdade
exige autorização de trabalho num país específico.

A categorização também é frouxa. Uma amostra de 36 vagas da Remotive em
`category=data` devolveu, entre outras, um "AI Cinematic Video Editor" e um
"Product Sales Specialist".

O resultado é que responder *"quais vagas de Data Engineer abertas agora aceitam
alguém no Brasil, e o que elas estão pedindo?"* exige ler centenas de anúncios à
mão, toda semana, para descartar 80% deles.

## A abordagem

Cinco estágios, com o trabalho caro no fim da fila:

```
fetch     RemoteOK · Remotive · We Work Remotely · Himalayas · HN Who-is-hiring
          API e RSS públicos — sem scraping, sem browser, sem CAPTCHA
   │
filter    elegibilidade geográfica · dedupe · plausibilidade de cargo
          determinístico, custo zero — derruba ~80% do volume
   │
score     LLM pontua 1-10 contra o perfil e extrai skills, senioridade,
          faixa salarial e modelo de contrato, em lotes de 20 vagas
   │
radar     agregação SQL sobre o histórico: skills mais pedidas, tendência
          mês a mês, mediana salarial, gap contra o perfil
   │
review    fila ordenada por nota, para decisão humana
```

O filtro determinístico roda **antes** do estágio com LLM. Essa ordem é o
controle de custo do pipeline: só ~20% das vagas coletadas chegam ao modelo.

O estado vive num SQLite. Como as skills são gravadas por vaga com data, o radar
é uma série temporal e não um retrato — dá para perguntar se dbt subiu nos
últimos três meses, não só quantas vagas pedem dbt hoje.

## Stack

| Camada | Ferramenta |
|---|---|
| Linguagem | Python 3.11+ |
| Armazenamento | SQLite |
| Extração de skills | Claude via CLI headless (`claude -p`) |
| Orquestração | cron → **Airflow** (Fase 6) |
| Transformações | SQL → **dbt** (Fase 6) |
| Testes | pytest, sobre fixtures de payloads reais |

Sem dependência de serviço pago: todas as fontes são APIs públicas e a extração
usa uma assinatura existente, não cobrança por token.

## Roadmap

| Fase | Escopo | Status |
|---|---|---|
| 1 | `fetch` + `filter` + schema | 🚧 em andamento |
| 2 | `radar` v0 — skills por regex | ⏳ |
| 3 | Perfil configurável | ⏳ |
| 4 | `score` via LLM | ⏳ |
| 5 | `radar` v1 — tendência, salário | ⏳ |
| 6 | Airflow + dbt | ⏳ |
| 7 | Geração de documentos por vaga | ⏳ |

## Configuração

O perfil usado na pontuação fica em `perfil.yaml`, que **não é versionado** —
contém dados pessoais. Um `perfil.example.yaml` documenta o formato.

## Licença

MIT
