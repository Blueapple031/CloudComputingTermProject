#!/usr/bin/env bash
# EC2에서 git pull → docker build → docker run (ECR 불필요)
# 사용: bash git-deploy.sh
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/CloudComputingTermProject}"
REPO_URL="${REPO_URL:-https://github.com/Blueapple031/CloudComputingTermProject.git}"
BRANCH="${BRANCH:-2026-06-01-thze}"
IMAGE_NAME="${IMAGE_NAME:-dummy-web:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-dummy-web}"
PORT="${PORT:-8000}"

if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone -b "$BRANCH" "$REPO_URL" "$REPO_DIR"
else
  cd "$REPO_DIR"
  git fetch origin
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
fi

cd "$REPO_DIR/services/dummy-web"
docker build -t "$IMAGE_NAME" .

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "${PORT}:8000" \
  -e INSTANCE_ID="${INSTANCE_ID:-dummy-ec2}" \
  "$IMAGE_NAME"

sleep 2
curl -fsS "http://localhost:${PORT}/health"
echo ""
echo "[git-deploy] dummy-web 완료 — http://$(curl -s ifconfig.me 2>/dev/null || echo LOCAL):${PORT}"
