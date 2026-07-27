# radar-vagas

Pipeline de dados que agrega vagas remotas de cinco fontes públicas, resolve
elegibilidade geográfica, extrai skills exigidas com LLM e produz um relatório
de tendência do mercado.

> 🚧 Em construção. Coleta, filtro e relatório funcionando; pontuação por LLM
> é a próxima fase — ver [Roadmap](#roadmap).

```console
$ radar-vagas coletar
coletadas    662
aprovadas    69

fonte         coletadas  aprovadas
gupy                 63         57
remotive             36          7
hn                  276          3
wwr                  87          2
remoteok            100          0
himalayas           100          0
```

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
fetch     Gupy · RemoteOK · Remotive · We Work Remotely · Himalayas · HN
          API e RSS públicos — sem scraping, sem browser, sem CAPTCHA
   │
filter    modalidade (100% remoto) · elegibilidade geográfica · dedupe ·
          plausibilidade de cargo — determinístico, custo zero
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
| 1 | `fetch` + `filter` + schema | ✅ |
| 2 | `radar` v0 — skills por regex, relatório semanal | ✅ |
| 3 | Perfil configurável | ⏳ |
| 4 | `score` via LLM | ⏳ |
| 5 | `radar` v1 — tendência, salário | ⏳ |
| 6 | Airflow + dbt | ⏳ |
| 7 | Geração de documentos por vaga | ⏳ |

## Uso

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/radar-vagas coletar          # busca, filtra e grava
.venv/bin/radar-vagas review --links   # lista as vagas pendentes
.venv/bin/radar-vagas relatorio        # escreve a nota da semana
.venv/bin/radar-vagas descartar 7      # marca como descartada
.venv/bin/radar-vagas aplicada 13      # marca como aplicada
```

## Configuração

| Variável | Default | O que faz |
|---|---|---|
| `RADAR_DB` | `vagas.db` | Caminho do SQLite |
| `RADAR_RELATORIOS` | `relatorios/` | Onde os relatórios semanais são escritos |

O perfil usado na pontuação fica em `perfil.yaml`, que **não é versionado** —
contém dados pessoais. Os relatórios gerados também ficam fora do git: carregam
empresa, faixa salarial e às vezes contato.

## Testes

```bash
.venv/bin/pytest        # 95 testes, todos contra fixtures — nenhum toca a rede
```

## Licença

MIT
