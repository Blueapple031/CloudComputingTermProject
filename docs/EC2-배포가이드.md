# EC2 배포 가이드 (Phase 1 — EC2 2대)

> **1회 배포만 쉽게:** Ubuntu EC2 초기 상태 기준 분리 메뉴얼  
> - [EC2-Dummy-설정.md](./EC2-Dummy-설정.md) ← **먼저**  
> - [EC2-Attacker-설정.md](./EC2-Attacker-설정.md) ← Dummy Private IP 필요  
> - [EC2-배포-README.md](./EC2-배포-README.md) — 문서 안내

아래는 CI/CD·bootstrap 포함 **전체** 가이드이다. 로컬 `docker compose` 로 검증한 뒤 AWS에 올린다.

| EC2 | 서비스 | 포트 |
|-----|--------|------|
| EC2 #1 | attacker-web | 8080 |
| EC2 #2 | dummy-web | 8000 |

---

## 0. 사전 준비 체크리스트

- [ ] AWS 계정 + 리전 결정 (예: `ap-northeast-2` 서울)
- [ ] GitHub 레포에 코드 push
- [ ] 로컬에서 `docker compose -f deploy/docker-compose.yml up --build` 동작 확인
- [ ] SSH 키 페어 (.pem) 생성·보관

---

## 1. ECR 리포지토리 생성

AWS 콘솔 → **ECR** → 리포지토리 생성 (2개):

- `dummy-web`
- `attacker-web`

레지스트리 URL 예시:

```text
123456789012.dkr.ecr.ap-northeast-2.amazonaws.com
```

이 값을 `ECR_REGISTRY` 로 사용한다.

---

## 2. EC2 2대 생성

| 항목 | EC2 #1 (Attacker) | EC2 #2 (Dummy) |
|------|-------------------|----------------|
| 이름 태그 | attacker | dummy |
| AMI | Amazon Linux 2023 | 동일 |
| 타입 | t3.small | t3.small (또는 t3.micro) |
| 키 페어 | 동일 PEM | 동일 PEM |
| VPC | 같은 VPC (기본 VPC 가능) | 동일 |
| Public IP | 할당 (SSH·UI용) | 할당 |

**IAM Role (권장)** — EC2 생성 시 연결:

- 정책: `AmazonEC2ContainerRegistryReadOnly` (ECR pull)
- Actions용 IAM 사용자는 별도 (ECR push 권한)

---

## 3. Security Group

### SG-dummy (EC2 #2)

| 방향 | 포트 | 소스 |
|------|------|------|
| Inbound | 8000 | SG-attacker (또는 EC2 #1 private IP) |
| Inbound | 22 | 내 IP (SSH) |
| Outbound | 전체 | 0.0.0.0/0 |

### SG-attacker (EC2 #1)

| 방향 | 포트 | 소스 |
|------|------|------|
| Inbound | 8080 | 내 IP (브라우저 UI) |
| Inbound | 22 | 내 IP (SSH) |
| Outbound | 8000 | SG-dummy (또는 EC2 #2 private IP) |
| Outbound | 전체 | 0.0.0.0/0 (ECR pull) |

> Phase 1: Attacker → Dummy **Private IP** 로 통신하는 것이 안전하다.

---

## 4. EC2 최초 셋업 (각 서버 1회)

SSH 접속 후 레포 clone (또는 deploy 파일만 scp).

### 4.1 공통: bootstrap

```bash
# EC2 #2 (dummy) 예시
ssh -i your.pem ec2-user@<DUMMY_PUBLIC_IP>

git clone https://github.com/<YOUR_ORG>/CloudComputingTermProject.git
cd CloudComputingTermProject
bash infra/scripts/bootstrap-ec2.sh dummy   # attacker EC2 에서는 attacker

# docker 그룹 적용 (로그아웃 후 재접속 또는)
newgrp docker
```

### 4.2 deploy 파일 배치

**EC2 #2 (dummy-web):**

```bash
sudo mkdir -p /opt/app/dummy-web/deploy
sudo cp -r services/dummy-web/deploy/* /opt/app/dummy-web/deploy/
sudo cp services/dummy-web/deploy/docker-compose.prod.yml /opt/app/dummy-web/
sudo cp services/dummy-web/.env.example /opt/app/dummy-web/.env
sudo chown -R ec2-user:ec2-user /opt/app/dummy-web

# .env 편집
nano /opt/app/dummy-web/.env
```

`.env` 예시:

```env
INSTANCE_ID=dummy-ec2-1
DEFAULT_LOAD_MS=100
```

**EC2 #1 (attacker-web):** 동일하게 `/opt/app/attacker-web/` 에 복사.

`.env` 예시 (Dummy **Private IP** 로 수정):

```env
TARGET_URL=http://10.0.1.23:8000/api/load?ms=100
ALLOWED_TARGET_HOSTS=10.0.1.23,localhost,127.0.0.1
MAX_RPS=5000
```

> `10.0.1.23` 은 EC2 #2 의 **Private IPv4** (콘솔에서 확인).

---

## 5. 이미지 배포 (2가지 방법)

### 방법 A — GitHub Actions (권장)

1. GitHub → Settings → Secrets → Actions:

| Secret | 값 |
|--------|-----|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `DUMMY_EC2_HOST` | EC2 #2 public IP 또는 DNS |
| `ATTACKER_EC2_HOST` | EC2 #1 public IP |
| `EC2_SSH_USER` | `ec2-user` |
| `EC2_SSH_PRIVATE_KEY` | .pem 전체 내용 |
| `ECR_REGISTRY` | (선택) Actions 가 ecr-login 으로 자동 설정 가능 |

2. `main` 브랜치에 push (워크플로가 `main` 기준)

   - `services/dummy-web/**` 변경 → `deploy-dummy.yml`
   - `services/attacker-web/**` 변경 → `deploy-attacker.yml`

3. Actions 탭에서 배포 성공 확인

> 다른 브랜치만 쓰는 경우: `.github/workflows/deploy-*.yml` 의 `branches: [main]` 을 본인 브랜치로 수정.

### 방법 B — 수동 (첫 배포·Actions 전)

**로컬 PC**에서:

```powershell
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <ECR_REGISTRY>

docker build -t <ECR_REGISTRY>/dummy-web:latest services/dummy-web
docker push <ECR_REGISTRY>/dummy-web:latest

docker build -t <ECR_REGISTRY>/attacker-web:latest services/attacker-web
docker push <ECR_REGISTRY>/attacker-web:latest
```

**EC2 #2**에서:

```bash
export ECR_REGISTRY=123456789012.dkr.ecr.ap-northeast-2.amazonaws.com
export IMAGE_TAG=latest
export AWS_REGION=ap-northeast-2
bash /opt/app/dummy-web/deploy/deploy.sh
```

**EC2 #1**에서 동일 (`attacker-web`).

---

## 6. 동작 확인

### EC2 #2 (dummy)

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/metrics
```

브라우저: `http://<DUMMY_PUBLIC_IP>:8000` → CPU 대시보드

### EC2 #1 (attacker)

브라우저: `http://<ATTACKER_PUBLIC_IP>:8080`

- 대상 URL이 Dummy Private IP 인지 확인
- RPS 50~100 으로 **시작** → Dummy 대시보드 CPU 상승

### 연결 안 될 때

- Security Group: Attacker → Dummy 8000 허용 여부
- `TARGET_URL` / `ALLOWED_TARGET_HOSTS` 에 Dummy **Private IP** 포함 여부
- Dummy 컨테이너 실행: `docker ps`

---

## 7. 구조 요약

```text
[브라우저] → EC2#1:8080 attacker UI
                 ↓ HTTP (VPC private)
            EC2#2:8000 dummy-web (/api/load)
```

```text
[개발자 push] → GitHub Actions → ECR push → SSH → EC2 deploy.sh → docker pull & up
```

---

## 8. 비용·운영 팁

- 실험 끝나면 EC2 **중지(stop)** — 과금 절감
- Budget Alert 설정
- SSH 22번은 **본인 IP만** 허용

---

## 9. 다음 단계 (Phase 2)

- Dummy 앞에 ALB 추가
- ASG + Launch Template (dummy-web 동일 이미지)
- attacker `TARGET_URL` → ALB DNS 로 변경
- `ALLOWED_TARGET_HOSTS` 에 ALB 호스트명 추가
