# HidroMeter

Sistema de telemetria de hidrômetros — detecção de vazamento, comparação de consumo, previsão e recomendações de economia de água para condomínios. Projeto acadêmico (Software Product: Analysis, Specification, Project & Implementation) com intenção de evoluir para produto real.

## Estrutura do repositório

```
plano-projeto-hidrometro.md   # visão geral, schema, entregas
docs/
  personas.md                 # síndico e morador
  requisitos.md                # requisitos funcionais e não funcionais
  decisoes-tecnicas.md        # decisões técnicas e o porquê
backend/                      # Node.js + Express + Prisma (API REST)
frontend/                     # React
simulator/                    # script gerador do dataset histórico simulado
analysis/                     # scripts Python (pandas) — detecção, previsão, recomendações
```

## Status

Em planejamento/estruturação — ver `plano-projeto-hidrometro.md` para o roadmap de entregas.

## Stack

- Backend: Node.js + Express + Prisma
- Banco: PostgreSQL (Docker)
- Frontend: React
- Análise de dados: Python (pandas)
- Auth: JWT + bcrypt
