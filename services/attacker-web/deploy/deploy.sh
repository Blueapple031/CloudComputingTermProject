#!/usr/bin/env bash
# attacker-web EC2 #1 배포 스크립트 (dummy-web/deploy/deploy.sh 와 동일 패턴)
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/app/attacker-web}"
COMPOSE_FILE="${APP_DIR}/docker-compose.prod.yml"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "[deploy] attacker-web 시작 — dir=${APP_DIR} tag=${IMAGE_TAG}"

if [[ -z "${ECR_REGISTRY:-}" ]]; then
  echo "[deploy] ERROR: ECR_REGISTRY 환경변수가 필요합니다." >&2
  exit 1
fi

cd "${APP_DIR}"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

export ECR_REGISTRY IMAGE_TAG

docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d

sleep 2
curl -fsS "http://localhost:8080/health" | head -c 200
echo ""
echo "[deploy] attacker-web 배포 완료"
