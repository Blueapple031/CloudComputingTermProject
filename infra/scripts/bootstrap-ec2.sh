#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# EC2 최초 1회 셋업 스크립트
#
# Amazon Linux 2023 / Ubuntu 에서 실행:
#   curl -fsSL ... | bash
#   또는 repo clone 후: sudo bash infra/scripts/bootstrap-ec2.sh attacker|dummy
#
# 설치 항목: Docker, Docker Compose plugin, AWS CLI, /opt/app 디렉터리
# ─────────────────────────────────────────────────────────────
set -euo pipefail

ROLE="${1:-}"  # attacker | dummy

if [[ "${ROLE}" != "attacker" && "${ROLE}" != "dummy" ]]; then
  echo "Usage: bootstrap-ec2.sh [attacker|dummy]" >&2
  exit 1
fi

echo "[bootstrap] role=${ROLE}"

# ── OS 감지 ──
if command -v dnf &>/dev/null; then
  sudo dnf update -y
  sudo dnf install -y docker git curl
elif command -v apt-get &>/dev/null; then
  sudo apt-get update
  sudo apt-get install -y docker.io git curl
else
  echo "[bootstrap] 지원하지 않는 OS" >&2
  exit 1
fi

# ── Docker 기동 ──
sudo systemctl enable --now docker
sudo usermod -aG docker "${USER}" || true

# ── Docker Compose plugin ──
if ! docker compose version &>/dev/null; then
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -SL "https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

# ── AWS CLI (ECR pull 용) ──
if ! command -v aws &>/dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  sudo /tmp/aws/install
fi

# ── 앱 디렉터리 ──
APP_NAME="${ROLE}-web"
sudo mkdir -p "/opt/app/${APP_NAME}/deploy"
sudo chown -R "${USER}:${USER}" /opt/app

echo "[bootstrap] 완료. 다음 단계:"
echo "  1. deploy/docker-compose.prod.yml, deploy/deploy.sh, .env 를 /opt/app/${APP_NAME}/ 에 복사"
echo "  2. ECR_REGISTRY 환경변수 설정 후 deploy.sh 실행"
echo "  3. (선택) docker 그룹 적용: newgrp docker"
