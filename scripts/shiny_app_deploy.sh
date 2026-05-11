#!/usr/bin/env bash
set -euo pipefail

JUMP_HOST="${SHINY_JUMP_HOST:-}"
VM_HOST="${SHINY_VM_HOST:-192.168.122.149}"
OPERATOR="${SHINY_OPERATOR:-droubi}"
MAINTAINER="${SHINY_MAINTAINER:-kevinnovak}"
BASE_DIR="${SHINY_BASE_DIR:-/srv/shiny-server}"
PUBLIC_BASE_URL="${SHINY_PUBLIC_BASE_URL:-http://shiny.labfsg.intra}"

usage() {
  cat <<'USAGE'
Uso:
  bash scripts/shiny_app_deploy.sh CAMINHO_DO_APP [nome-do-app]
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Erro: comando obrigatorio ausente: %s\n' "$1" >&2
    exit 1
  fi
}

validate_app_dir() {
  local app_dir="$1"
  if [[ ! -d "$app_dir" ]]; then
    printf 'Erro: diretorio nao encontrado: %s\n' "$app_dir" >&2
    exit 1
  fi
  if [[ -f "$app_dir/app.R" ]]; then
    return
  fi
  if [[ -f "$app_dir/ui.R" && -f "$app_dir/server.R" ]]; then
    return
  fi
  printf 'Erro: o app precisa ter app.R ou ui.R + server.R em %s\n' "$app_dir" >&2
  exit 1
}

normalize_app_name() {
  local raw_name="$1"
  printf '%s' "$raw_name" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/[^a-z0-9._-]//g'
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage >&2
    exit 1
  fi

  require_cmd ssh
  require_cmd scp
  require_cmd curl
  require_cmd basename

  local source_dir="$1"
  validate_app_dir "$source_dir"

  local app_name
  if [[ $# -eq 2 ]]; then
    app_name="$(normalize_app_name "$2")"
  else
    app_name="$(normalize_app_name "$(basename "$source_dir")")"
  fi

  [[ -n "$app_name" ]] || { echo 'Erro: nome de app vazio.' >&2; exit 1; }

  local abs_source_dir
  abs_source_dir="$(cd "$source_dir" && pwd)"
  local stage_name
  stage_name="shiny-deploy-${app_name}-$(date '+%Y%m%d-%H%M%S')-$$"

  SSH_COMMON_OPTS=( -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null )
  if [[ -n "$JUMP_HOST" && "$JUMP_HOST" != "none" ]]; then
    SSH_COMMON_OPTS+=( -o ProxyJump="$JUMP_HOST" )
  fi

  scp "${SSH_COMMON_OPTS[@]}" -r "$abs_source_dir" "${OPERATOR}@${VM_HOST}:${stage_name}"

  ssh "${SSH_COMMON_OPTS[@]}" -tt "${OPERATOR}@${VM_HOST}" \
    "STAGE_NAME='${stage_name}' APP_NAME='${app_name}' MAINTAINER='${MAINTAINER}' BASE_DIR='${BASE_DIR}' bash -s" <<'EOF_REMOTE'
set -euo pipefail
STAGE_PATH="$HOME/$STAGE_NAME"
TARGET_PATH="$BASE_DIR/$APP_NAME"

sudo usermod -aG shiny "$MAINTAINER"
sudo chgrp shiny "$BASE_DIR"
sudo chmod 2775 "$BASE_DIR"
sudo mkdir -p "$TARGET_PATH"
sudo find "$TARGET_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
sudo cp -a "$STAGE_PATH/." "$TARGET_PATH/"
sudo chown -R "$MAINTAINER:shiny" "$TARGET_PATH"
sudo find "$TARGET_PATH" -type d -exec chmod 2775 {} \;
sudo find "$TARGET_PATH" -type f -exec chmod 664 {} \;
rm -rf "$STAGE_PATH"

curl -fsSI --max-time 15 "http://127.0.0.1:3838/$APP_NAME/" | sed -n '1,8p'
EOF_REMOTE

  curl -fsSI --max-time 15 --resolve "shiny.labfsg.intra:80:150.162.76.60" "${PUBLIC_BASE_URL}/${app_name}/" | sed -n '1,8p'
}

main "$@"
