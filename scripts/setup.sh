#!/usr/bin/env bash
#
# setup.sh — instala o Docker Engine + o plugin Docker Compose e deixa o
# projeto pré-configurado. Roda uma vez por máquina.
#
# É idempotente: pode ser executado várias vezes sem estragar nada. NUNCA
# sobrescreve um .env já existente. Depois de rodar, preencha o .env e use
# ./scripts/start.sh.
#
# Uso:
#   ./scripts/setup.sh          # instala e pré-configura
#   ./scripts/setup.sh --help
#
# Suporta: Ubuntu/Debian (método oficial via apt) e demais distros Linux
# (script oficial de conveniência get.docker.com). macOS: aponta o Docker
# Desktop (instalação manual).
set -Eeuo pipefail

# --- localização do repositório (funciona a partir de qualquer diretório) ---
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

CRED_FILE="camera-dados-meteorologicos-1d6806cf7e78.json"  # bind-mount do compose

# --- logging (com cor quando o terminal suporta) ---
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
  C_INFO="$(tput setaf 4)"; C_OK="$(tput setaf 2)"; C_WARN="$(tput setaf 3)"
  C_ERR="$(tput setaf 1)"; C_RST="$(tput sgr0)"
else
  C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""; C_RST=""
fi
info() { printf '%s[setup]%s %s\n' "$C_INFO" "$C_RST" "$*"; }
ok()   { printf '%s[ ok ]%s %s\n' "$C_OK" "$C_RST" "$*"; }
warn() { printf '%s[aviso]%s %s\n' "$C_WARN" "$C_RST" "$*" >&2; }
err()  { printf '%s[erro]%s %s\n' "$C_ERR" "$C_RST" "$*" >&2; }
die()  { err "$*"; exit 1; }

trap 'err "Falhou na linha $LINENO (veja a mensagem acima)."' ERR

case "${1:-}" in
  -h|--help)
    sed -n '3,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  "") ;;
  *) die "Opção desconhecida: $1  (use --help)" ;;
esac

# --- só instala automaticamente no Linux ---
OS="$(uname -s)"
if [ "$OS" != "Linux" ]; then
  if [ "$OS" = "Darwin" ]; then
    die "macOS detectado. Instale o Docker Desktop (inclui o Compose):
     https://docs.docker.com/desktop/install/mac-install/
   Depois rode: ./scripts/start.sh"
  fi
  die "SO '$OS' não é suportado por este instalador automático.
   Instale o Docker manualmente: https://docs.docker.com/engine/install/"
fi

# --- helper de sudo (root não precisa) ---
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
elif command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  die "Não sou root e não há 'sudo'. Rode como root ou instale o sudo."
fi

# --- helper de download (curl ou wget) ---
download() { # $1=url  $2=arquivo_saida
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$2" "$1"
  else
    die "Preciso de 'curl' ou 'wget' para baixar. Instale um deles e rode de novo."
  fi
}

docker_ok() { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }

# --- método oficial Ubuntu/Debian (repositório apt) ---
install_docker_apt() {
  local id_like distro codename
  # shellcheck disable=SC1091
  . /etc/os-release
  case "${ID:-}" in
    ubuntu) distro="ubuntu" ;;
    debian) distro="debian" ;;
    *)
      # derivadas (Mint, Pop!_OS, etc.): usam o repo da base
      id_like="${ID_LIKE:-}"
      case "$id_like" in
        *ubuntu*) distro="ubuntu" ;;
        *)        distro="debian" ;;
      esac
      ;;
  esac
  codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
  if [ -z "$codename" ]; then
    warn "Não detectei o codename da distro; usando o script de conveniência."
    install_docker_convenience
    return
  fi

  info "Removendo pacotes Docker conflitantes (se houver)…"
  $SUDO apt-get remove -y docker.io docker-doc docker-compose docker-compose-v2 \
    podman-docker containerd runc >/dev/null 2>&1 || true

  info "Configurando o repositório oficial do Docker ($distro / $codename)…"
  export DEBIAN_FRONTEND=noninteractive
  # Um repositório pré-existente quebrado (PPA expirado etc.) não deve matar a
  # instalação; seguimos e caímos no fallback adiante se o repo do Docker falhar.
  $SUDO apt-get update -y || warn "apt-get update reclamou (provável repositório pré-existente quebrado); seguindo."
  $SUDO apt-get install -y ca-certificates curl
  $SUDO install -m 0755 -d /etc/apt/keyrings
  $SUDO curl -fsSL "https://download.docker.com/linux/$distro/gpg" \
    -o /etc/apt/keyrings/docker.asc
  $SUDO chmod a+r /etc/apt/keyrings/docker.asc

  # Formato deb822 (.sources) — o atual na doc oficial.
  $SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/$distro
Suites: $codename
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

  # Se o repo do Docker não atualiza (ex.: codename de derivada sem suite
  # correspondente, como kali-rolling) ou a instalação falha, cai no script de
  # conveniência oficial em vez de abortar.
  if ! $SUDO apt-get update -y; then
    warn "apt-get update falhou para o repo do Docker (codename '$codename' pode não existir lá); usando o script de conveniência."
    install_docker_convenience
    return
  fi
  info "Instalando docker-ce, cli, containerd, buildx e compose…"
  if ! $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin; then
    warn "Instalação via apt falhou; usando o script de conveniência."
    install_docker_convenience
  fi
}

# --- fallback oficial cross-distro (get.docker.com) ---
install_docker_convenience() {
  local tmp rc=0
  tmp="$(mktemp)"
  info "Baixando o script oficial de conveniência (get.docker.com)…"
  download "https://get.docker.com" "$tmp"
  info "Executando o instalador do Docker…"
  $SUDO sh "$tmp" || rc=$?
  rm -f "$tmp"                     # limpa mesmo se o instalador falhar
  [ "$rc" -eq 0 ] || die "O instalador do Docker (get.docker.com) falhou (código $rc)."
}

# --- 1) Docker Engine + Compose ---
if docker_ok; then
  ok "Docker + Compose já instalados ($(docker --version 2>/dev/null | sed 's/,.*//'))."
else
  info "Docker/Compose ausentes — instalando…"
  # shellcheck disable=SC1091
  . /etc/os-release 2>/dev/null || true
  case "${ID:-}:${ID_LIKE:-}" in
    ubuntu:*|debian:*|*:*ubuntu*|*:*debian*) install_docker_apt ;;
    *)
      warn "Distro '${ID:-desconhecida}' sem método apt oficial aqui; usando get.docker.com."
      install_docker_convenience
      ;;
  esac
  docker_ok || die "A instalação terminou mas 'docker compose' ainda não funciona. Veja o log acima."
  ok "Docker instalado."
fi

# --- 2) serviço no boot (systemd) ---
if command -v systemctl >/dev/null 2>&1; then
  if $SUDO systemctl enable --now docker.service >/dev/null 2>&1; then
    ok "Serviço docker habilitado e ativo."
  else
    warn "Não consegui habilitar/iniciar o serviço docker via systemd; verifique manualmente."
  fi
fi

# --- 3) uso sem sudo: grupo 'docker' ---
# Alvo = o operador real: SUDO_USER quando rodou via 'sudo ./setup.sh', senão
# USER, senão 'id -un'. Os defaults (:-) evitam 'unbound variable' com set -u em
# ambientes sem USER exportado (CI, docker run -u, su -c). Roda mesmo como root
# (via sudo) para não deixar o humano de fora do grupo; pula só quando o alvo é
# o próprio root (que não precisa).
NEED_RELOGIN=0
TARGET_USER="${SUDO_USER:-${USER:-$(id -un)}}"
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
  getent group docker >/dev/null 2>&1 || $SUDO groupadd docker || true
  if id -nG "$TARGET_USER" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
    ok "Usuário '$TARGET_USER' já está no grupo docker."
  else
    info "Adicionando '$TARGET_USER' ao grupo docker (uso sem sudo)…"
    if $SUDO usermod -aG docker "$TARGET_USER"; then
      NEED_RELOGIN=1
    else
      warn "Não consegui adicionar '$TARGET_USER' ao grupo docker; o start.sh usará sudo se preciso."
    fi
  fi
fi

# --- 4) pré-configuração do projeto ---
cd "$REPO_DIR"

if [ -f .env ]; then
  ok ".env já existe — mantido (não sobrescrevo)."
elif [ -f .env.example ]; then
  cp .env.example .env
  chmod 600 .env 2>/dev/null || true   # .env guarda segredos (chaves/JWT/senha)
  ok ".env criado a partir de .env.example — EDITE antes de subir."
else
  warn ".env.example não encontrado; não consegui criar o .env."
fi

mkdir -p logs && ok "Pasta logs/ pronta."

if [ -f "$CRED_FILE" ]; then
  ok "Credencial Google encontrada (./$CRED_FILE)."
else
  warn "Credencial Google ausente: coloque o JSON da service account em
     ./$CRED_FILE  (as tools de Google Sheets/Calendar dependem dele)."
fi

# --- resumo ---
echo
ok "Setup concluído."
info "Próximos passos:"
info "  1) Edite o .env e preencha GEMINI_API_KEY (obrigatório p/ o chat) e"
info "     WINDY_API_KEY (previsão do tempo)."
info "  2) Garanta o JSON da service account em ./$CRED_FILE (Sheets/Calendar)."
info "  3) Rode:  ./scripts/start.sh"
if [ "$NEED_RELOGIN" -eq 1 ]; then
  echo
  warn "Você foi adicionado ao grupo 'docker'. Saia e entre na sessão de novo
     (ou rode 'newgrp docker') para usar o docker sem sudo. Enquanto isso,
     o start.sh detecta e usa sudo automaticamente."
fi
