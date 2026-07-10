#!/usr/bin/env bash
#
# start.sh — valida a configuração e sobe a stack (db + backend + frontend).
# Rode DEPOIS de ter o Docker instalado (./scripts/setup.sh) e o .env preenchido.
#
# Uso:
#   ./scripts/start.sh            # build + up (em segundo plano) + checagens
#   ./scripts/start.sh --no-build # sobe sem reconstruir as imagens (mais rápido)
#   ./scripts/start.sh --help
set -Eeuo pipefail

# --- localização do repositório (funciona a partir de qualquer diretório) ---
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

CRED_FILE="camera-dados-meteorologicos-1d6806cf7e78.json"
API_URL="http://localhost:8000"
FRONT_URL="http://localhost:5173"

# --- logging ---
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
  C_INFO="$(tput setaf 4)"; C_OK="$(tput setaf 2)"; C_WARN="$(tput setaf 3)"
  C_ERR="$(tput setaf 1)"; C_RST="$(tput sgr0)"
else
  C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""; C_RST=""
fi
info() { printf '%s[start]%s %s\n' "$C_INFO" "$C_RST" "$*"; }
ok()   { printf '%s[ ok ]%s %s\n' "$C_OK" "$C_RST" "$*"; }
warn() { printf '%s[aviso]%s %s\n' "$C_WARN" "$C_RST" "$*" >&2; }
err()  { printf '%s[erro]%s %s\n' "$C_ERR" "$C_RST" "$*" >&2; }
die()  { err "$*"; exit 1; }

trap 'err "Falhou na linha $LINENO (veja a mensagem acima)."' ERR

# --- argumentos ---
BUILD=1
case "${1:-}" in
  -h|--help)
    sed -n '3,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  -n|--no-build) BUILD=0 ;;
  "") ;;
  *) die "Opção desconhecida: $1  (use --help)" ;;
esac

# --- Docker disponível? ---
command -v docker >/dev/null 2>&1 \
  || die "Docker não encontrado. Rode ./scripts/setup.sh primeiro."
docker compose version >/dev/null 2>&1 \
  || die "Plugin 'docker compose' não encontrado. Rode ./scripts/setup.sh."
[ -f docker-compose.yml ] \
  || die "docker-compose.yml não encontrado em $REPO_DIR."

# --- consigo falar com o daemon? (senão, tenta sudo) ---
DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
    warn "Sem permissão direta no daemon; usando 'sudo docker'.
     (Saia/entre da sessão após o setup para usar sem sudo.)"
    DOCKER="sudo docker"
  else
    die "Não consigo falar com o daemon do Docker. Ele está rodando?
   Tente:  sudo systemctl start docker"
  fi
fi

# --- .env existe? ---
[ -f .env ] || die ".env não encontrado.
   Rode ./scripts/setup.sh (ou 'cp .env.example .env') e preencha as chaves."

# lê o valor de uma chave do .env SEM dar 'source' (evita executar conteúdo)
env_val() { # $1 = chave
  local v
  v="$(grep -E "^[[:space:]]*$1=" .env | tail -n1 | cut -d= -f2- || true)"
  v="${v%$'\r'}"                     # remove CR (arquivos salvos no Windows)
  v="${v#\"}"; v="${v%\"}"            # tira aspas duplas nas bordas
  v="${v#\'}"; v="${v%\'}"            # tira aspas simples nas bordas
  v="${v#"${v%%[![:space:]]*}"}"     # trim espaços à esquerda
  v="${v%"${v##*[![:space:]]}"}"     # trim espaços à direita (valor só de espaços -> vazio)
  printf '%s' "$v"
}

# --- validação da configuração ---
BLOQUEIO=0
if [ -n "$(env_val GEMINI_API_KEY)" ]; then
  ok "GEMINI_API_KEY definido."
else
  err "GEMINI_API_KEY vazio no .env — o chat NÃO vai funcionar."
  BLOQUEIO=1
fi

if [ -n "$(env_val WINDY_API_KEY)" ]; then
  ok "WINDY_API_KEY definido."
else
  warn "WINDY_API_KEY vazio — a tool de previsão do tempo ficará indisponível."
fi

# O bind-mount do compose aponta para este arquivo; se ele faltar, o daemon do
# Docker cria um DIRETÓRIO (root) no lugar — irrecuperável com 'cp'. Então:
# detecta o diretório e aborta com instrução; se faltar, deixa um placeholder
# de ARQUIVO (do usuário) para o Docker não criar o tal diretório.
if [ -e "$CRED_FILE" ] && [ ! -f "$CRED_FILE" ]; then
  die "'./$CRED_FILE' existe mas NÃO é um arquivo comum — provável diretório criado
   pelo Docker num run anterior sem o JSON. Remova e coloque o arquivo real:
     sudo rm -rf ./$CRED_FILE"
elif [ -s "$CRED_FILE" ]; then
  ok "Credencial Google presente (./$CRED_FILE)."
else
  warn "Credencial Google ausente ou vazia (./$CRED_FILE): as tools de Google
     Sheets/Calendar vão falhar até você colocar o JSON real aqui."
  if [ ! -e "$CRED_FILE" ]; then
    if : > "$CRED_FILE" 2>/dev/null; then
      info "Criei ./$CRED_FILE vazio (placeholder) — substitua pelo JSON real."
    else
      warn "Não consegui criar o placeholder ./$CRED_FILE (verifique permissões)."
    fi
  fi
fi

[ -n "$(env_val GOOGLE_CALENDAR_ID)" ] \
  || info "GOOGLE_CALENDAR_ID vazio — tool de agenda desativada (opcional)."

if [ "$BLOQUEIO" -ne 0 ]; then
  if [ -t 0 ]; then
    printf '%sContinuar mesmo assim? [s/N] %s' "$C_WARN" "$C_RST" >&2
    read -r resp
    case "$resp" in
      s|S|sim|Sim|y|Y|yes) ;;
      *) die "Abortado. Ajuste o .env e rode de novo." ;;
    esac
  else
    die "Configuração incompleta (GEMINI_API_KEY). Ajuste o .env e rode de novo."
  fi
fi

# --- aviso de portas em uso ---
if command -v ss >/dev/null 2>&1; then
  for p in 5173 8000 5432; do
    if ss -ltn 2>/dev/null | grep -q ":$p "; then
      warn "Porta $p já está em uso — se não for esta própria stack, pode haver conflito."
    fi
  done
fi

mkdir -p logs

# --- subir a stack ---
if [ "$BUILD" -eq 1 ]; then
  info "Construindo e subindo os serviços (docker compose up --build -d)…"
  $DOCKER compose up --build -d
else
  info "Subindo os serviços sem rebuild (docker compose up -d)…"
  $DOCKER compose up -d
fi

# --- esperar o backend responder ---
if command -v curl >/dev/null 2>&1; then
  info "Aguardando o backend em $API_URL …"
  pronto=0
  for _ in $(seq 1 60); do
    if curl -fsS "$API_URL/openapi.json" >/dev/null 2>&1; then pronto=1; break; fi
    sleep 2
  done
  if [ "$pronto" -eq 1 ]; then
    ok "Backend no ar."
  else
    warn "Backend não respondeu em ~120s. Acompanhe: $DOCKER compose logs -f backend"
    # Em execução não-interativa (CI), um bring-up que não sobe deve falhar (exit != 0),
    # senão o job passa verde com a stack morta.
    [ -t 1 ] || exit 1
  fi
else
  info "curl indisponível — pulando a checagem de saúde do backend."
fi

# --- resumo ---
echo
ok "Stack no ar."
info "  Frontend:      $FRONT_URL"
info "  API (docs):    $API_URL/docs"
info "  Login padrão:  admin / admin"
info "  Ver logs:      $DOCKER compose logs -f            (ou: ... logs -f backend)"
info "  Parar tudo:    $DOCKER compose down"
