# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Consulte a documentação oficial atual antes de escrever código

**Antes de escrever qualquer código que use uma biblioteca, SDK ou API externa, confirme a API vigente na documentação oficial** (WebFetch/web) em vez de confiar na memória de treino, que pode estar desatualizada. Já aconteceu neste projeto: a API atual do SDK `google-genai` divergia do que o conhecimento antigo indicava, e só foi acertada consultando a doc oficial. Vale sobretudo para dependências que mudam rápido (google-genai, FastAPI, Pydantic v2, Tailwind v4, Vite 6). Na dúvida sobre assinatura, parâmetros ou nomes de modelo, busque a doc oficial primeiro.

## Comandos

- **Subir tudo:** `docker compose up --build` → frontend em http://localhost:5173, docs da API em http://localhost:8000/docs. Usuário padrão: **admin / admin**.
- **Após adicionar dependência Python:** rebuild da imagem do backend — `docker compose up -d --build backend`. O bind mount faz hot-reload do **código**, mas dependências instaladas vivem na **imagem**; sem rebuild elas não aparecem. Mesma regra para dependência nova no frontend.
- **Logs:** `docker compose logs -f <serviço>` (`backend`, `frontend`, `db`).
- **Testes e lint/formatter não existem** neste projeto — não há pytest, ruff, eslint, prettier nem configs equivalentes. Não invente comandos de teste/lint.

## Arquitetura

Projeto de exemplo (login + chat) com frontend React, backend FastAPI e Postgres, orquestrado por Docker Compose. O que exige ler vários arquivos:

- **Fluxo de variáveis de ambiente (ler 3 arquivos):** `.env` (raiz) é consumido pelo **docker-compose** para substituição de variáveis e injetado no processo via o bloco `backend.environment`; o código lê com `os.getenv` puro em `backend/app/config.py` (sem pydantic-settings e sem dotenv no Python). **Consequência:** uma variável que esteja no `.env` mas **não** listada em `backend.environment` do `docker-compose.yml` **não chega** ao Python. Adicionar uma env var do backend significa mexer em três lugares: `.env`/`.env.example`, `docker-compose.yml` e `config.py`.

- **Backend (FastAPI, `backend/app/`):** `main.py` usa um `lifespan` que espera o Postgres subir, cria as tabelas e semeia o usuário padrão (`seed.py`). O CORS é restrito a `FRONTEND_ORIGIN`. As rotas ficam sob o prefixo `/api`, divididas em routers (`routers/auth.py`, `routers/chat.py`) incluídos no `main.py`.

- **Autenticação:** o login valida credenciais no Postgres com hash **bcrypt** (`passlib`) e emite um **JWT**; rotas protegidas dependem de `get_current_user` (`security.py`, via `OAuth2PasswordBearer`), que decodifica o token e carrega o `User`. Para proteger um endpoint novo, adote a mesma dependência.

- **Persistência:** SQLAlchemy + Postgres, com a sessão aberta por request pela dependência `get_db` (`database.py`). A única entidade é `User` (`models.py`); o **chat é stateless** — nenhuma mensagem é persistida.

- **Chat (agente com tools):** `routers/chat.py` delega para `agent.py`, que roda o loop de function calling do **Gemini (SDK `google-genai`, chave em `GEMINI_API_KEY` lida do ambiente)** com as tools registradas. Consulte a doc oficial do SDK antes de alterar a chamada.

- **Tools do agente (`backend/app/tools/`):** cada módulo de tool expõe `DECLARATIONS` (declarações para o modelo) e `FUNCTIONS` (dict nome → callable); o `tools/__init__.py` agrega tudo em `TOOL_DECLARATIONS`/`TOOL_FUNCTIONS`, consumidos por `agent.py`. Tool nova = módulo novo + 1 import e 2 spreads no `__init__.py`. Erros esperados retornam `{"erro": "..."}` (o modelo explica ao usuário). A credencial do Google Sheets entra no container por bind mount read-only em `/secrets/` (docker-compose) e está no `.gitignore` — nunca commitá-la.

- **Frontend (React + Vite + Tailwind CSS v4, JS/JSX, sem TypeScript):** `src/api.js` centraliza todas as chamadas ao backend (`fetch`, base em `VITE_API_URL`) — comece por aí ao mexer na integração. `App.jsx` guarda a sessão no `localStorage` e alterna entre `pages/Login.jsx` e `pages/Home.jsx`. O Tailwind v4 é configurado apenas via `@import "tailwindcss";` no CSS, sem arquivo de config.

- **Serviços (docker-compose):** `db` (Postgres, com healthcheck), `backend` (uvicorn com `--reload` + bind mount do código) e `frontend` (dev server do Vite). O backend só sobe após o `db` ficar saudável.

## Convenções

- Código, comentários, mensagens de UI e documentação estão em **português** — mantenha o padrão.
- Segredos ficam fora do controle de versão: o `.gitignore` cobre o `.env` e o JSON de credenciais do Google.
- O frontend não tem `package-lock.json` (usa `npm install`).
