# Backend

Python + FastAPI + SQLAlchemy (Alembic para migrations). 

## Setup

```bash
py -3.13 -m venv .venv          # Python 3.13 (a 3.14 pode não ter wheel de todo pacote ainda)
.venv\Scripts\activate            # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

cp .env.example .env              # ajuste DATABASE_URL/JWT_SECRET se necessário
alembic upgrade head
python seed.py                    # dados de demonstração (ver docs/entrega-1.md)

uvicorn app.main:app --reload --port 3001   # http://localhost:3001
```

Pré-requisito: Postgres rodando (`docker compose up -d` na raiz do repo).

Docs interativas da API (Swagger): `http://localhost:3001/docs`.

## Endpoints (Entrega 1)

- `POST /api/auth/register`, `POST /api/auth/login`
- `GET /api/condominios` (leitura, escopado por papel)
- `GET/POST/PUT/DELETE /api/blocos`
- `GET/POST/PUT/DELETE /api/unidades`
- `GET/POST/PUT/DELETE /api/hidrometros`

## Endpoints (Entrega 2)

- `POST /api/leituras`, `POST /api/leituras/lote` (síndico) — ingestão; calcula a vazão (L/h) e exige timestamp crescente e acumulado não decrescente (`409` caso contrário)
- `GET /api/leituras?hidrometroId=...` — leituras brutas paginadas (`limite`, `deslocamento`, `de`, `ate`)
- `GET /api/unidades/{id}/consumo?dias=30&agrupar=dia|hora` (ou `de`/`ate`) — consumo agregado para o gráfico

Para gerar o dataset histórico: `python ../simulator/simulate.py` (ver `simulator/README.md`).

Todas as rotas (exceto `/auth/*`) exigem `Authorization: Bearer <token>`. Escritas (`POST/PUT/DELETE`) exigem papel `sindico`. Listagens (`GET`) são filtradas automaticamente: síndico vê o(s) condomínio(s) que administra, morador vê apenas a(s) própria(s) unidade(s).

`POST /api/unidades` aceita `{ blocoId, numero }` (uma unidade) ou `{ blocoId, numeros: [...] }` (várias de uma vez); cada unidade criada já ganha seu hidrômetro automaticamente (1:1, `numeroSerie` derivado do id da unidade).

## Mexendo no schema

Os models SQLAlchemy (`app/models.py`) são a fonte única de verdade do banco. Depois de alterar um model:

```bash
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

Ver `docs/entrega-1.md` e `docs/entrega-2.md` para detalhes e `docs/requisitos.md` para os requisitos cobertos.
