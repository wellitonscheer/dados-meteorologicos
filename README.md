# dados-meteorologicos

CRUD simples de exemplo: tela de **login** + tela principal com um **chat**.
O chat é um **agente**: o **Gemini** (via SDK `google-genai`) decide quando usar as tools disponíveis — consulta à planilha Google Sheets "Dados Climáticos por Produtor" e previsão do tempo (Windy) — antes de responder.

## Stack

- **Frontend:** React + Vite + Tailwind CSS v4
- **Backend:** Python + FastAPI + SQLAlchemy
- **Banco:** PostgreSQL
- **Execução:** Docker Compose

## Como rodar

### Opção A — scripts (recomendado)

Em uma máquina Linux nova, dois scripts fazem tudo:

```bash
./scripts/setup.sh    # instala Docker + Compose e cria o .env a partir do exemplo
# edite o .env (GEMINI_API_KEY, WINDY_API_KEY) e coloque o JSON da service account
./scripts/start.sh    # valida a configuração e sobe a stack
```

- `setup.sh` — instala o Docker Engine + o plugin Compose (método oficial via apt no
  Ubuntu/Debian; script de conveniência get.docker.com nas demais distros), habilita
  o serviço, adiciona seu usuário ao grupo `docker` e cria o `.env` (sem sobrescrever
  um existente). É idempotente. macOS: instale o Docker Desktop e pule para o `start.sh`.
- `start.sh` — confere Docker/`.env`/credencial, avisa o que falta e roda
  `docker compose up --build -d` (use `--no-build` para subir sem reconstruir).

### Opção B — manual

```bash
cp .env.example .env      # defina GEMINI_API_KEY e WINDY_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- API (docs): http://localhost:8000/docs

Usuário padrão criado automaticamente: **admin / admin**.

### Tools do agente (Google Sheets e Windy)

- **Google Sheets:** coloque o JSON da service account na raiz do repositório com o nome `camera-dados-meteorologicos-1d6806cf7e78.json` (ou ajuste o volume no `docker-compose.yml`) e compartilhe a planilha "Dados Climáticos por Produtor" com `dados-sheets@camera-dados-meteorologicos.iam.gserviceaccount.com` (permissão de leitor basta). O arquivo está no `.gitignore` — nunca deve ser commitado.
- **Windy:** defina `WINDY_API_KEY` no `.env` (chave da [Point Forecast API](https://api.windy.com/point-forecast)).

## Como funciona

1. Login valida usuário/senha no Postgres (senha em hash bcrypt) e retorna um token JWT.
2. A tela principal mostra o usuário logado no topo e um campo de mensagem.
3. Ao enviar um texto, o backend chama o Gemini com a mensagem e retorna a resposta gerada (nada é persistido).

## Estrutura

- `backend/` — API FastAPI (`app/`), `Dockerfile`, `requirements.txt`
- `frontend/` — app React (Vite), `Dockerfile`
- `docker-compose.yml` — orquestra `db`, `backend` e `frontend`
