# dados-meteorologicos

CRUD simples de exemplo: tela de **login** + tela principal com um **chat**.
O chat encaminha a mensagem para o **Gemini** (via SDK `google-genai`) e retorna a resposta gerada.

## Stack

- **Frontend:** React + Vite + Tailwind CSS v4
- **Backend:** Python + FastAPI + SQLAlchemy
- **Banco:** PostgreSQL
- **Execução:** Docker Compose

## Como rodar

```bash
cp .env.example .env      # defina GEMINI_API_KEY para o chat funcionar
docker compose up --build
```

- Frontend: http://localhost:5173
- API (docs): http://localhost:8000/docs

Usuário padrão criado automaticamente: **admin / admin**.

## Como funciona

1. Login valida usuário/senha no Postgres (senha em hash bcrypt) e retorna um token JWT.
2. A tela principal mostra o usuário logado no topo e um campo de mensagem.
3. Ao enviar um texto, o backend chama o Gemini com a mensagem e retorna a resposta gerada (nada é persistido).

## Estrutura

- `backend/` — API FastAPI (`app/`), `Dockerfile`, `requirements.txt`
- `frontend/` — app React (Vite), `Dockerfile`
- `docker-compose.yml` — orquestra `db`, `backend` e `frontend`
