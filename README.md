# HidroMeter

Sistema de telemetria de hidrômetros — detecção de vazamento, comparação de consumo, previsão e recomendações de economia de água para condomínios. Projeto acadêmico (Software Product: Analysis, Specification, Project & Implementation) com intenção de evoluir para produto real.

## Estrutura do repositório

```
plano-projeto-hidrometro.md   # visão geral, schema, entregas
docs/
  personas.md                 # síndico e morador
  requisitos.md                # requisitos funcionais e não funcionais
  decisoes-tecnicas.md        # decisões técnicas e o porquê
backend/                      # Python + FastAPI + SQLAlchemy (API REST)
frontend/                     # React
simulator/                    # script gerador do dataset histórico simulado
analysis/                     # scripts Python (pandas) — detecção, previsão, recomendações
```

## Status

**Entrega 1 concluída** — cadastro básico (condomínios/blocos/unidades/hidrômetros) + autenticação com dois papéis (síndico/morador). Ver `docs/entrega-1.md` para o que foi implementado e como rodar/demonstrar, e `plano-projeto-hidrometro.md` para o roadmap das próximas entregas.

Setup rápido:

```bash
docker compose up -d                 # Postgres
cd backend && py -3.13 -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && cp .env.example .env && alembic upgrade head && python seed.py && uvicorn app.main:app --reload --port 3001
cd frontend && cp .env.example .env && npm install && npm run dev
```

## Stack

- Backend: Python + FastAPI + SQLAlchemy (Alembic)
- Banco: PostgreSQL (Docker)
- Frontend: React
- Análise de dados: Python (pandas) — processo separado do backend
- Auth: JWT + bcrypt
