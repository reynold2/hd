#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/www/dk_project/wwwroot/hd}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-https://github.com/reynold2/hd.git}"
SERVICE_NAME="${SERVICE_NAME:-hd-queue.service}"
DOMAIN="${DOMAIN:-hd.yxck3d.tech}"
ADMIN_BASE="${ADMIN_BASE:-/admin/}"
CUSTOMER_BASE="${CUSTOMER_BASE:-/customer/}"
API_BASE="${API_BASE:-}"
BACKEND_PORT="${BACKEND_PORT:-8020}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
NGINX_VHOST_DIR="${NGINX_VHOST_DIR:-/www/server/panel/vhost/nginx}"
ORIGIN_CERT_DIR="${ORIGIN_CERT_DIR:-/www/server/panel/vhost/letsencrypt/hd.yxck3d.tech}"
GITHUB_TOKEN_FILE="${GITHUB_TOKEN_FILE:-/root/.config/hd-queue/github_token}"
BUILD_SWAP_FILE="${BUILD_SWAP_FILE:-/www/swap-codex-build-hd}"
BUILD_SWAP_SIZE="${BUILD_SWAP_SIZE:-2G}"
NODE_OPTIONS_BUILD="${NODE_OPTIONS_BUILD:---max-old-space-size=1024}"
SKIP_CUSTOMER_H5_BUILD="${SKIP_CUSTOMER_H5_BUILD:-0}"
SKIP_MINIAPP_BUILD="${SKIP_MINIAPP_BUILD:-0}"

log() {
  printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

run() {
  log "$*"
  "$@"
}

require_file() {
  if [[ ! -f "$1" ]]; then
    printf 'Missing required file: %s\n' "$1" >&2
    exit 1
  fi
}

github_auth_args() {
  local token="${GITHUB_TOKEN:-}"
  if [[ -z "$token" && -f "$GITHUB_TOKEN_FILE" ]]; then
    token="$(tr -d '\r\n' < "$GITHUB_TOKEN_FILE")"
  fi

  if [[ -n "$token" ]]; then
    local basic_auth
    basic_auth="$(printf 'reynold2:%s' "$token" | base64 | tr -d '\n')"
    printf '%s\n' "-c" "http.version=HTTP/1.1" "-c" "http.https://github.com/.extraheader=AUTHORIZATION: Basic ${basic_auth}"
  fi
}

ensure_build_swap() {
  if [[ "$(id -u)" != "0" ]]; then
    log "Skipping swap setup because current user is not root"
    return
  fi

  if swapon --show=NAME --noheadings | grep -Fxq "$BUILD_SWAP_FILE"; then
    log "Build swap already enabled: ${BUILD_SWAP_FILE}"
    return
  fi

  if [[ ! -f "$BUILD_SWAP_FILE" ]]; then
    run fallocate -l "$BUILD_SWAP_SIZE" "$BUILD_SWAP_FILE"
    run chmod 600 "$BUILD_SWAP_FILE"
    run mkswap "$BUILD_SWAP_FILE"
  fi

  run swapon "$BUILD_SWAP_FILE"
  run free -h
}

ensure_repo() {
  if [[ -d "$APP_DIR/.git" ]]; then
    return
  fi

  if [[ -e "$APP_DIR" && -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    printf 'APP_DIR exists but is not an empty git repository: %s\n' "$APP_DIR" >&2
    printf 'Move it aside before first git-based deploy, for example: mv %s %s.backup-$(date +%%Y%%m%%d%%H%%M%%S)\n' "$APP_DIR" "$APP_DIR" >&2
    exit 1
  fi

  run mkdir -p "$(dirname "$APP_DIR")"
  mapfile -t auth_args < <(github_auth_args)
  run git "${auth_args[@]}" clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
}

git_pull_latest() {
  ensure_repo
  cd "$APP_DIR"
  mapfile -t auth_args < <(github_auth_args)
  run git "${auth_args[@]}" pull --ff-only "$REPO_URL" "$BRANCH"
  run git rev-parse --short HEAD
}

write_backend_env() {
  cd "$APP_DIR/backend"
  if [[ -f ".env" ]]; then
    return
  fi

  run mkdir -p "$APP_DIR/data"
  cat > .env <<EOF
DATABASE_URL=sqlite:////www/dk_project/wwwroot/hd/data/queue_calling.db
CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN}
EOF
}

install_backend() {
  cd "$APP_DIR/backend"
  write_backend_env
  if [[ ! -d ".venv" ]]; then
    run "$PYTHON_BIN" -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  set -a
  source .env
  set +a
  run python -m pip install -r requirements.txt
  stamp_existing_backend_schema
  run python -m alembic upgrade head
  run python -m app.seed_data
  run python -m compileall app
}

stamp_existing_backend_schema() {
  python <<'PY'
import os
from sqlalchemy import create_engine, inspect, text

database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url)
with engine.begin() as connection:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if "meal_sessions" not in tables or "alembic_version" in tables:
        raise SystemExit(0)
    connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260529_0002')"))
PY
}

install_service() {
  cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF
[Unit]
Description=HD Queue Calling FastAPI service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${APP_DIR}/backend
EnvironmentFile=${APP_DIR}/backend/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=${APP_DIR}/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT}
Restart=always
RestartSec=3
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
  run systemctl daemon-reload
  run systemctl enable "$SERVICE_NAME"
}

restart_backend() {
  install_service
  run systemctl restart "$SERVICE_NAME"
  run systemctl is-active "$SERVICE_NAME"
  wait_for_local_health
}

wait_for_local_health() {
  local url="http://127.0.0.1:${BACKEND_PORT}/health"
  local attempt
  for attempt in $(seq 1 30); do
    if curl -fsS "$url"; then
      return 0
    fi
    printf 'Waiting for backend health (%s/30)...\n' "$attempt"
    sleep 1
  done
  printf 'Backend health check did not become ready: %s\n' "$url" >&2
  systemctl --no-pager --full status "$SERVICE_NAME" >&2 || true
  journalctl -u "$SERVICE_NAME" -n 80 --no-pager >&2 || true
  exit 1
}

build_admin() {
  cd "$APP_DIR/merchant-admin"
  ensure_build_swap
  run npm ci
  log "npm run build -- --base=${ADMIN_BASE} (VITE_API_BASE=${API_BASE})"
  NODE_OPTIONS="$NODE_OPTIONS_BUILD" VITE_API_BASE="$API_BASE" npm run build -- --base="$ADMIN_BASE"
}

build_customer_h5() {
  if [[ "$SKIP_CUSTOMER_H5_BUILD" == "1" ]]; then
    log "Skipping customer H5 build because SKIP_CUSTOMER_H5_BUILD=1"
    return
  fi
  cd "$APP_DIR/customer-miniapp"
  run npm ci
  log "npm run build:h5 -- --base=${CUSTOMER_BASE} (VITE_API_BASE=${API_BASE})"
  VITE_API_BASE="$API_BASE" npm run build:h5 -- --base="$CUSTOMER_BASE"
}

build_miniapp() {
  if [[ "$SKIP_MINIAPP_BUILD" == "1" ]]; then
    log "Skipping WeChat miniapp build because SKIP_MINIAPP_BUILD=1"
    return
  fi
  cd "$APP_DIR/customer-miniapp"
  run npm ci
  log "npm run build:mp-weixin (VITE_API_BASE=https://${DOMAIN})"
  VITE_API_BASE="https://${DOMAIN}" npm run build:mp-weixin
  if grep -R "127\.0\.0\.1\|localhost\|/fh/api\|/fh/" -n dist/build/mp-weixin >/tmp/hd-miniapp-local-url.txt 2>/dev/null; then
    cat /tmp/hd-miniapp-local-url.txt >&2
    printf 'Miniapp build still contains local or old /fh URLs.\n' >&2
    exit 1
  fi
  if [[ ! -f "dist/build/mp-weixin/app.js" ]]; then
    printf 'Miniapp build artifact is missing: %s\n' "$APP_DIR/customer-miniapp/dist/build/mp-weixin/app.js" >&2
    exit 1
  fi
}

ensure_origin_cert() {
  if [[ -f "${ORIGIN_CERT_DIR}/fullchain.pem" && -f "${ORIGIN_CERT_DIR}/privkey.pem" ]]; then
    log "Origin certificate already exists: ${ORIGIN_CERT_DIR}"
    return
  fi

  run mkdir -p "$ORIGIN_CERT_DIR"
  run openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
    -keyout "${ORIGIN_CERT_DIR}/privkey.pem" \
    -out "${ORIGIN_CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}" \
    -addext "subjectAltName=DNS:${DOMAIN}"
  run chmod 600 "${ORIGIN_CERT_DIR}/privkey.pem"
}

reload_nginx() {
  local target_conf="${NGINX_VHOST_DIR}/${DOMAIN}.conf"
  ensure_origin_cert
  run cp "$APP_DIR/deploy/hd/nginx-hd.yxck3d.tech.conf" "$target_conf"
  run nginx -t
  run nginx -s reload
}

verify_public() {
  run curl -fsS "http://${DOMAIN}/health"
  run curl -fsSI "http://${DOMAIN}${ADMIN_BASE}"
  run curl -fsSI "http://${DOMAIN}${CUSTOMER_BASE}"
  if curl -fsSI "https://${DOMAIN}${CUSTOMER_BASE}" >/dev/null 2>&1; then
    log "Cloudflare HTTPS is reachable: https://${DOMAIN}${CUSTOMER_BASE}"
  else
    log "HTTPS check did not pass from origin shell. Confirm Cloudflare SSL mode and proxy status before submitting the WeChat domain."
  fi
  log "Deployment finished. Admin: https://${DOMAIN}${ADMIN_BASE}"
  log "Customer H5: https://${DOMAIN}${CUSTOMER_BASE}"
  log "Miniapp request domain: https://${DOMAIN}"
}

main() {
  git_pull_latest
  install_backend
  restart_backend
  build_admin
  build_customer_h5
  build_miniapp
  reload_nginx
  verify_public
}

main "$@"
