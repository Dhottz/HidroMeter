# Projeto — Sistema de telemetria de hidrômetros

> Disciplina: Software Product — Analysis, Specification, Project & Implementation
> Projeto acadêmico com intenção de evoluir para produto real (inspirado no NIVELio).

## Visão geral

Sistema que coleta leituras de hidrômetros com telemetria (simuladas via sensores de pulso, sem hardware físico neste momento), armazena em banco relacional, e a partir dos dados tratados gera:
- Detecção de vazamento (consumo anômalo, baseline adaptativo por unidade)
- Comparação/ranking de consumo entre unidades
- Previsão de consumo futuro
- Recomendações de economia de água

Dois papéis de usuário:
- **Síndico**: visão agregada de auditoria — todas as unidades/blocos do condomínio que administra.
- **Morador**: visão restrita — apenas os dados da(s) própria(s) unidade(s).

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy (Alembic para migrations)
- **Banco**: PostgreSQL (Docker)
- **Frontend**: React
- **Análise de dados**: Python (pandas), processo separado do backend (mesma linguagem, mas continuam sendo dois processos distintos), lendo/escrevendo no mesmo Postgres
- **Simulador**: script que gera um dataset histórico de uma vez (não é um processo contínuo por enquanto)
- **Autenticação**: JWT + bcrypt para hash de senha

## Modelagem de dados (schema alvo)

```
condominios (id, nome, endereco)
blocos (id, nome, condominio_id)
unidades (id, numero, bloco_id)
hidrometros (id, unidade_id, numero_serie, litros_por_pulso default 1)
leituras (id, hidrometro_id, timestamp, litros_acumulados, vazao_instantanea)

usuarios (id, nome, email, senha_hash, papel [sindico|morador], criado_em)
usuario_condominios (usuario_id, condominio_id)   -- acesso de síndico
usuario_unidades (usuario_id, unidade_id)         -- acesso de morador

alertas (id, hidrometro_id, timestamp, tipo, severidade, descricao, baseline_referencia, vazao_detectada)
recomendacoes (id, unidade_id, timestamp, texto, categoria)
```

Notas:
- `litros_acumulados` é cumulativo (tipo odômetro — nunca zera); consumo por período = diferença entre leituras.
- `vazao_instantanea` é **campo derivado**: `(litros_acumulados_atual - litros_acumulados_anterior) / tempo_decorrido`. Não é um dado bruto do sensor (ver `docs/decisoes-tecnicas.md`).
- `usuario_condominios` e `usuario_unidades` são N:N — um síndico pode administrar mais de um condomínio, um morador pode ter mais de uma unidade.

## Estrutura de escala (dados de simulação)

- 1 condomínio, 3 blocos, ~50 unidades por bloco (≈150 unidades no total)
- 3 meses de histórico (90 dias)
- Leituras horárias (ajustável para 15min depois se precisar de mais granularidade)
- 10 unidades com vazamento injetado (padrão de vazão constante mesmo na janela noturna, ver detecção abaixo)

## Detecção de vazamento — baseline adaptativo por unidade

Técnica: **Minimum Night Flow (MNF)** — a mesma usada por companhias de água/sistemas AMI reais.

- Janela de referência: madrugada (ex: 00h–05h), quando o uso legítimo de água é ~zero.
- Para cada unidade, calcula-se a mediana da vazão noturna dos últimos 7–14 dias (baseline própria da unidade, não um valor fixo global).
- Se a vazão noturna atual ultrapassa significativamente esse baseline (ex: 3x) por N noites seguidas → gera alerta, com severidade escalando conforme desvio e duração.
- Vantagem sobre threshold fixo: cada unidade tem seu próprio "normal" (evita falso positivo em unidade com uso noturno legítimo, ex: irrigação automática).

## Princípio das entregas

Cada entrega é uma fatia vertical completa — envolve banco, backend e frontend juntos, nunca uma camada isolada. Cada entrega deve ser demonstrável de ponta a ponta.

## Entrega 1 — Cadastro básico + autenticação

- **Banco**: `condominios`, `blocos`, `unidades`, `hidrometros`, `usuarios`, `usuario_condominios`, `usuario_unidades`
- **Backend**: auth (registro/login, JWT), CRUD de unidades/hidrômetros, middleware de autorização por papel (síndico vs morador)
- **Frontend**: tela de login, listagem/cadastro de unidades (visão filtrada por papel)

## Entrega 2 — Leituras simuladas

- **Banco**: `leituras`
- **Backend**: endpoint de ingestão de leituras + simulador que gera dataset histórico completo (padrão realista: picos manhã/noite, quase zero de madrugada, 10 unidades com vazamento injetado)
- **Frontend**: gráfico de consumo por unidade/período

## Entrega 3 — Detecção de vazamento e comparação

- **Banco**: `alertas`
- **Backend**: rotina de análise MNF com baseline adaptativo por unidade, persiste alertas
- **Frontend**: tela de alertas ativos (síndico vê todos do condomínio, morador só os da própria unidade) + ranking de consumo entre unidades (síndico)

## Entrega 4 — Previsão e recomendações

- **Banco**: `recomendacoes`
- **Backend**: endpoint que roda modelo de previsão simples (regressão) sobre o histórico e gera recomendações baseadas em regras
- **Frontend**: tela de recomendações personalizadas por unidade/morador

## Notas gerais para implementação

- Simulador gera o dataset histórico de uma vez (3 meses) — não depende de hardware físico em nenhum momento.
- A análise de dados em Python (pandas) roda como processo separado, lendo do mesmo Postgres, alimentando `alertas` e `recomendacoes`.
- Manter o schema dos models (SQLAlchemy) como fonte única de verdade do banco.
- Documentar cada entrega com: o que foi implementado, decisões técnicas, e print/demo do fluxo funcionando.
- Ver `docs/` para personas, requisitos e decisões técnicas detalhadas (material de análise/especificação da disciplina).
