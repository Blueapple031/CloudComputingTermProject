#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# dummy-web EC2 배포 스크립트
#
# GitHub Actions (deploy-dummy.yml) 가 SSH 로 EC2 #2 에 접속해 실행한다.
# 로컬 EC2 에서 수동 배포할 때도 동일하게 사용 가능.
#
# 사전 조건:
#   - Docker, Docker Compose, AWS CLI 설치 (bootstrap-ec2.sh)
#   - /opt/app/dummy-web/docker-compose.prod.yml, .env 존재
#   - EC2 IAM Role 또는 credential 으로 ECR pull 가능
#
# 환경변수:
#   ECR_REGISTRY  (필수) ECR 레지스트리 URL
#   IMAGE_TAG     (선택) 기본값 latest
#   AWS_REGION    (선택) 기본값 ap-northeast-2
# ─────────────────────────────────────────────────────────────
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/app/dummy-web}"
COMPOSE_FILE="${APP_DIR}/docker-compose.prod.yml"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "[deploy] dummy-web 시작 — dir=${APP_DIR} tag=${IMAGE_TAG}"

if [[ -z "${ECR_REGISTRY:-}" ]]; then
  echo "[deploy] ERROR: ECR_REGISTRY 환경변수가 필요합니다." >&2
  exit 1
fi

cd "${APP_DIR}"

# ECR 로그인 — EC2 IAM Role 사용 시 aws cli 만 있으면 됨
echo "[deploy] ECR 로그인..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

export ECR_REGISTRY IMAGE_TAG

echo "[deploy] 이미지 pull..."
docker compose -f "${COMPOSE_FILE}" pull

echo "[deploy] 컨테이너 기동..."
docker compose -f "${COMPOSE_FILE}" up -d

# 헬스체크 — 실패 시 CI 배포 실패로 표시
echo "[deploy] 헬스체크..."
sleep 2
curl -fsS "http://localhost:8000/health" | head -c 200
echo ""
echo "[deploy] dummy-web 배포 완료"
