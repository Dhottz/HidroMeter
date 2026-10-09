# Entrega 2 — Leituras simuladas

## O que foi implementado

Fatia vertical completa (banco + backend + simulador + frontend), conforme `plano-projeto-hidrometro.md`.

**Banco de dados** (`backend/app/models.py`):
- Tabela `leituras` (`id`, `hidrometro_id`, `timestamp`, `litros_acumulados`, `vazao_instantanea`), com `UNIQUE (hidrometro_id, timestamp)` — o índice dessa constraint atende as consultas por hidrômetro e período — e `ON DELETE CASCADE` a partir do hidrômetro
- Migration Alembic `a3f1c2d4b5e6_leituras` (RNF03)

**Backend** (`backend/app/routers/leituras.py`, `consumo.py`):
- `POST /api/leituras` e `POST /api/leituras/lote` — ingestão de leituras (RF07), restrita a síndico e validada contra o escopo dele. Calcula e persiste a `vazao_instantanea` (L/h) a partir da leitura anterior (RF08). O lote é "tudo ou nada"
- Validações: o timestamp deve ser posterior à última leitura do hidrômetro e o contador acumulado não pode diminuir (é um odômetro) — caso contrário `409`
- `GET /api/leituras?hidrometroId=&de=&ate=&limite=&deslocamento=` — leituras brutas, paginadas (RNF05), mais recentes primeiro; síndico só nos hidrômetros do condomínio, morador só nos da própria unidade
- `GET /api/unidades/{id}/consumo?dias=|de=&ate=&agrupar=hora|dia` — consumo em litros por hora ou dia (RF09). O consumo de cada leitura é a diferença para a anterior; sem `de`/`ate` usa os últimos `dias` (padrão 30) contados a partir da leitura mais recente da unidade. Morador de outra unidade recebe `403`
- Cálculo da vazão isolado em `app/services/leituras.py`, compartilhado com o simulador; checagem de escopo em `app/services/acesso.py`

**Simulador** (`simulator/simulate.py`, RNF04):
- Completa cada bloco do primeiro condomínio até 50 unidades (cada uma com hidrômetro) e grava 90 dias de leituras horárias — ≈ 324 mil linhas com 3 blocos
- Padrão realista: consumo diário por unidade proporcional ao nº de moradores (1–5, ~150 L/pessoa/dia), picos de manhã (6–9h) e à noite (18–22h), quase zero de madrugada, um pouco mais no fim de semana, ruído gaussiano
- 10 unidades sorteadas recebem vazamento: vazão extra constante de 4–12 L/h, todas as horas (inclusive a madrugada), começando entre 25% e 80% do período
- Gabarito dos vazamentos em `simulator/vazamentos_injetados.json` (gerado; fora do git) — serve para validar a detecção da Entrega 3
- Reexecutável: apaga e regrava as leituras dos hidrômetros; mesma `--seed` + mesmo `--fim` produzem o mesmo dataset

**Frontend** (`frontend/src/pages/ConsumoPage.jsx`):
- Nova rota `/consumo` (link "Consumo" na navbar) com gráfico de barras (Recharts) do consumo por unidade e período
- Seletor de unidade (síndico: todas, agrupadas por bloco; morador: só as próprias), período 7/30/90 dias ou datas personalizadas, agrupamento por dia ou hora (hora só até 14 dias, para o gráfico continuar legível)
- Resumo: total no período, média por hora/dia e maior consumo

## Requisitos cobertos

RF07, RF08, RF09, RNF03, RNF04, RNF05 (ver `docs/requisitos.md`).

## Como rodar / demonstrar

```bash
docker compose up -d
cd backend
.venv\Scripts\activate
alembic upgrade head
python seed.py                              # só se o banco estiver vazio — apaga os dados existentes
python ../simulator/simulate.py             # ~30 s; opções: --dias 90 --seed 42 --fim 2026-10-01
uvicorn app.main:app --reload --port 3001

cd ../frontend
npm install                                 # novo: recharts
npm run dev
```

Fluxo demonstrado: login como síndico → "Consumo" → escolhe uma unidade → alterna entre 7/30/90 dias e dia/hora (picos de manhã/noite e vale na madrugada visíveis no agrupamento por hora). Login como morador → só enxerga a própria unidade; `GET /api/unidades/<outra>/consumo` devolve `403`.

Validado na API: morador em unidade alheia `403`; morador tentando `POST /api/leituras` `403`; leitura com acumulado menor que o anterior ou timestamp não posterior `409`. Na amostra gerada, a vazão média na madrugada (1h–4h) foi ≈ 6 L/h na unidade com vazamento contra ≈ 0,4–0,8 L/h nas normais.

## Decisões pontuais desta entrega

- Ver decisão 6 em `docs/decisoes-tecnicas.md` (timestamps em horário local, sem fuso) e a decisão 1 (vazão derivada, em L/h, calculada na ingestão).
- Ingestão exige login de síndico: não há ainda credencial de dispositivo/gateway; como os sensores são simulados, o simulador grava direto no banco usando os mesmos models e a mesma função de cálculo de vazão da API.
- O consumo por período é calculado em Python (e não com `date_trunc`) para o endpoint não depender de função específica do Postgres; para 90 dias de uma unidade são ~2 mil linhas.
- Pendência herdada da Entrega 1: `alembic check` aponta diferença nas `UniqueConstraint` de `usuario_condominios`/`usuario_unidades` (declaradas no model mas não na migration `init`). Não afeta a tabela `leituras`.
