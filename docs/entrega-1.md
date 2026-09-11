# Entrega 1 — Cadastro básico + autenticação

## O que foi implementado

Fatia vertical completa (banco + backend + frontend) cobrindo autenticação e cadastro básico, conforme `plano-projeto-hidrometro.md`.

**Banco de dados** (`backend/app/models.py`, Postgres via Docker):
- `condominios`, `blocos`, `unidades`, `hidrometros`
- `usuarios` (papel `sindico` ou `morador`)
- `usuario_condominios` e `usuario_unidades` (tabelas de junção N:N de acesso — RF03/RF04)
- Schema versionado via Alembic (`backend/alembic/versions/`)
- `backend/seed.py` popula um cenário de demonstração (1 condomínio, 3 blocos, 9 unidades com hidrômetro cada, 1 síndico e 2 moradores)

**Backend** (Python + FastAPI + SQLAlchemy, `backend/app/`):
- `POST /api/auth/register` e `POST /api/auth/login` — JWT + bcrypt (RF01, RNF01, RNF02)
- Middleware `authenticate` (valida JWT) e `carregarEscopo`/`requireRole` (resolve os condomínios do síndico ou as unidades do morador e aplica autorização por papel — RF02, RF03, RF04)
- CRUD de `blocos`, `unidades` e `hidrometros`, todas as escritas restritas a síndico e validadas contra o escopo dele (RF05); listagens (`GET`) filtradas automaticamente pelo papel de quem está logado (RF06)
- `POST /api/unidades` cria uma ou várias unidades de uma vez (`numero` ou `numeros: [...]`), e cada unidade já nasce com seu próprio hidrômetro (`numeroSerie` derivado do id da unidade) — não existe cadastro manual de hidrômetro separado, já que nesta escala do projeto é sempre 1:1
- `GET /api/condominios` (somente leitura) para o frontend saber em qual condomínio o síndico pode cadastrar blocos

**Frontend** (React + Vite, `frontend/src/`):
- Tela de login (`LoginPage`) — autentica e guarda o JWT
- Tela de unidades (`UnidadesPage`) — síndico vê todas as unidades do condomínio agrupadas por bloco, com formulário para cadastrar bloco, edição inline do nome do bloco e remoção de unidade; morador vê somente a(s) própria(s) unidade(s), sem controles de edição
- Cadastro de unidades em dois modos: **por andar** (padrão comum de prédio — informa andar inicial, andar final e quantidade de apartamentos por andar, e o sistema gera "101, 102, 103, 201, 202, 203..." sozinho) ou **lista manual** (números avulsos separados por vírgula, para numeração fora do padrão). Os dois modos reaproveitam o mesmo `POST /api/unidades` em lote; cada unidade criada já ganha seu hidrômetro automaticamente
- `AuthContext` guarda o token no `localStorage`; rotas privadas redirecionam para `/login` se não autenticado

## Requisitos cobertos

RF01, RF02, RF03, RF04, RF05, RF06, RNF01, RNF02, RNF03 (ver `docs/requisitos.md`).

## Como rodar / demonstrar

```bash
# 1. Banco (Postgres via Docker)
docker compose up -d

# 2. Backend
cd backend
py -3.13 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 3001   # API em http://localhost:3001

# 3. Frontend (outro terminal)
cd frontend
cp .env.example .env
npm install
npm run dev               # SPA em http://localhost:5173
```

Credenciais de demonstração (seed), senha `senha123` para todas:
- **Síndico**: `sindico@hidrometer.com` — vê todas as unidades/blocos do "Residencial Águas Claras", pode cadastrar/remover blocos, unidades e hidrômetros.
- **Morador**: `morador1@hidrometer.com` — vê apenas a unidade A01, somente leitura.
- **Morador**: `morador2@hidrometer.com` — vê apenas a unidade B01, somente leitura.

Fluxo demonstrado: login como síndico → cadastro de bloco/unidade/hidrômetro → logout → login como morador → confirma que só enxerga a própria unidade e não tem controles de cadastro. No nível da API, autorização por papel confirmada via teste direto (morador tentando `POST /api/unidades` recebe `403`; requisição sem token recebe `401`).

## Decisões pontuais desta entrega

- Nomes de tabela/coluna no Postgres seguem snake_case (`unidade_id`, `numero_serie`, `senha_hash`, etc.), mapeados a partir de models SQLAlchemy também em snake_case; a resposta JSON da API sai em camelCase (`blocoId`, `numeroSerie`...) via um schema Pydantic base com `alias_generator` — mantém o contrato que o frontend já consome sem exigir nada especial do lado do banco.
- Endpoint `GET /api/condominios` foi adicionado (não estava explícito no plano) porque o frontend precisa saber em qual condomínio o síndico pode cadastrar o primeiro bloco; é somente leitura e reaproveita o mesmo escopo de autorização das demais rotas.
- `register` aceita `condominioId` (síndico) ou `unidadeId` (morador) diretamente no corpo da requisição, assumindo que esses registros já existem (criados pelo síndico ou via seed) — não há tela de "criar condomínio" nesta entrega, escopo definido no plano geral.
