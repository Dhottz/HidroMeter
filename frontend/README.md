# Frontend

React + Vite.

## Setup

```bash
cp .env.example .env    # VITE_API_URL, default aponta pro backend local
npm install
npm run dev              # http://localhost:5173
```

Pré-requisito: backend rodando em `http://localhost:3001` (ver `backend/README.md`).

## Telas (Entrega 1)

- **Login** (`/login`) — autentica e guarda o JWT.
- **Unidades** (`/unidades`, protegida) — listagem filtrada por papel: síndico vê todas as unidades/blocos do condomínio administrado com formulários de cadastro (bloco/unidade/hidrômetro) e ações de remover; morador vê somente a(s) própria(s) unidade(s), somente leitura.

Ver `docs/entrega-1.md` para credenciais de demonstração e fluxo completo.
