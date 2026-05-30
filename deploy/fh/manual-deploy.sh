#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/www/dk_project/wwwroot/fh}"
REPO_URL="${REPO_URL:-https://github.com/reynold2/hd.git}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-fh-queue.service}"
BACKEND_PORT="${BACKEND_PORT:-8020}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
NGINX_CONF="${NGINX_CONF:-/www/server/panel/vhost/nginx/extension/8.141.105.10/fh.conf}"
ADMIN_ROOT="${ADMIN_ROOT:-/www/wwwroot/fh/admin}"
CUSTOMER_ROOT="${CUSTOMER_ROOT:-/www/wwwroot/fh/customer}"
DATA_DIR="${DATA_DIR:-/www/dk_project/wwwroot/fh/data}"
DATABASE_URL="${DATABASE_URL:-sqlite:////www/dk_project/wwwroot/fh/data/queue_calling.db}"
VITE_API_BASE="/fh"

log() {
  printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

run() {
  log "$*"
  "$@"
}

ensure_repo() {
  if [[ -d "$APP_DIR/.git" ]]; then
    return
  fi
  if [[ -e "$APP_DIR" && -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    printf 'APP_DIR exists and is not an empty git repository: %s\n' "$APP_DIR" >&2
    exit 1
  fi
  run mkdir -p "$(dirname "$APP_DIR")"
  run git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
}

git_pull_latest() {
  ensure_repo
  cd "$APP_DIR"
  run git fetch origin "$BRANCH"
  run git checkout "$BRANCH"
  run git pull --ff-only origin "$BRANCH"
  run git rev-parse --short HEAD
}

install_backend() {
  cd "$APP_DIR/backend"
  run mkdir -p "$DATA_DIR"
  cat > .env <<EOF
DATABASE_URL=${DATABASE_URL}
CORS_ORIGINS=http://8.141.105.10
EOF
  if [[ ! -d ".venv" ]]; then
    run "$PYTHON_BIN" -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  run python -m pip install -r requirements.txt
  run python -m alembic upgrade head
  run python -m app.seed_data
  run python -m compileall app
}

install_service() {
  cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF
[Unit]
Description=FH Queue Calling FastAPI service
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
  run systemctl restart "$SERVICE_NAME"
}

wait_for_backend() {
  local url="http://127.0.0.1:${BACKEND_PORT}/health"
  for attempt in $(seq 1 30); do
    if curl -fsS "$url"; then
      return 0
    fi
    printf 'Waiting for backend health (%s/30)...\n' "$attempt"
    sleep 1
  done
  systemctl --no-pager --full status "$SERVICE_NAME" >&2 || true
  journalctl -u "$SERVICE_NAME" -n 80 --no-pager >&2 || true
  exit 1
}

build_frontends() {
  cd "$APP_DIR/merchant-admin"
  run npm ci
  log "VITE_API_BASE=/fh npm run build -- --base=/fh/admin/"
  VITE_API_BASE="/fh" npm run build -- --base=/fh/admin/

  cd "$APP_DIR/customer-miniapp"
  run npm ci
  log "VITE_API_BASE=/fh npm run build:h5 -- --base=/fh/customer/"
  VITE_API_BASE="/fh" npm run build:h5 -- --base=/fh/customer/
}

publish_static() {
  run mkdir -p "$ADMIN_ROOT" "$CUSTOMER_ROOT"
  run rsync -a --delete "$APP_DIR/merchant-admin/dist/" "$ADMIN_ROOT/"
  run rsync -a --delete "$APP_DIR/customer-miniapp/dist/build/h5/" "$CUSTOMER_ROOT/"
}

write_nginx_conf() {
  run mkdir -p "$(dirname "$NGINX_CONF")"
  cat > "$NGINX_CONF" <<EOF
location = /fh {
    return 301 /fh/admin/;
}

location ^~ /fh/health {
    proxy_pass http://127.0.0.1:${BACKEND_PORT}/health;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
}

location ^~ /fh/api/ {
    proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
}

location = /fh/admin {
    return 301 /fh/admin/;
}

location ^~ /fh/admin/ {
    alias ${ADMIN_ROOT}/;
    try_files \$uri \$uri/ /fh/admin/index.html;
}

location = /fh/customer {
    return 301 /fh/customer/;
}

location ^~ /fh/customer/ {
    alias ${CUSTOMER_ROOT}/;
    try_files \$uri \$uri/ /fh/customer/index.html;
}
EOF
  run nginx -t
  run nginx -s reload
}

verify_public() {
  run curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health"
  run curl -fsS "http://8.141.105.10/fh/health"
  run curl -fsSI "http://8.141.105.10/fh/admin/"
  run curl -fsSI "http://8.141.105.10/fh/customer/"
  log "Manual deploy finished: http://8.141.105.10/fh/admin/ and http://8.141.105.10/fh/customer/"
}

main() {
  git_pull_latest
  install_backend
  install_service
  wait_for_backend
  build_frontends
  publish_static
  write_nginx_conf
  verify_public
}

main "$@"
