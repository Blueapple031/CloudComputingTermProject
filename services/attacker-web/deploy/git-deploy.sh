#!/usr/bin/env bash
# EC2에서 git pull → docker build → docker run (ECR 불필요)
# 사용: DUMMY_PRIVATE_IP=172.31.x.x bash git-deploy.sh
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/CloudComputingTermProject}"
REPO_URL="${REPO_URL:-https://github.com/Blueapple031/CloudComputingTermProject.git}"
BRANCH="${BRANCH:-2026-06-01-thze}"
IMAGE_NAME="${IMAGE_NAME:-attacker-web:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-attacker-web}"
PORT="${PORT:-8080}"

if [[ -z "${DUMMY_PRIVATE_IP:-}" ]]; then
  echo "ERROR: DUMMY_PRIVATE_IP 환경변수 필요 (Dummy EC2 Private IP)" >&2
  echo "예: DUMMY_PRIVATE_IP=172.31.33.104 bash git-deploy.sh" >&2
  exit 1
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone -b "$BRANCH" "$REPO_URL" "$REPO_DIR"
else
  cd "$REPO_DIR"
  git fetch origin
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
fi

cd "$REPO_DIR/services/attacker-web"
docker build -t "$IMAGE_NAME" .

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${PORT}:8080" \
  -e TARGET_URL="http://${DUMMY_PRIVATE_IP}:8000/api/load?ms=100" \
  -e ALLOWED_TARGET_HOSTS="${DUMMY_PRIVATE_IP}" \
  -e MAX_RPS=5000 \
  "$IMAGE_NAME"

sleep 2
curl -fsS "http://localhost:${PORT}/health"
echo ""
echo "[git-deploy] attacker-web 완료 — http://$(curl -s ifconfig.me 2>/dev/null || echo LOCAL):${PORT}"
