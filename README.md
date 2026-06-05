# CloudComputingTermProject

DDoS 부하 실험 및 오토스케일링 관측용 실습 환경 (교육 목적).

## 구조

| 서비스 | EC2 | 포트 | 역할 |
|--------|-----|------|------|
| `dummy-web` | #2 | 8000 | 부하 수신 (`/api/load`) |
| `attacker-web` | #1 | 8080 | 부하 생성 UI/API |

## 로컬 실행

```bash
docker compose -f deploy/docker-compose.yml up --build
```

- Attacker UI: http://localhost:8080
- Dummy 상태: http://localhost:8000

## 테스트

```bash
cd services/dummy-web
pip install -r requirements.txt -r requirements-dev.txt
pytest -v

cd ../attacker-web
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

## EC2 배포 (Phase 2 ASG 아키텍처 기준)

두 서비스의 배포 패러다임이 다릅니다. 자세한 아키텍처는 [개발계획서.md](./개발계획서.md)의 8.1 섹션을 참고하세요.

### 1. Attacker Web (단일 EC2 - Push 배포)
1. ECR 리포지토리 `attacker-web` 생성
2. EC2 #1 접속 후 `bash infra/scripts/bootstrap-ec2.sh attacker` 실행
3. EC2 내부 `/opt/app/attacker-web/` 에 `deploy/` 스크립트 및 `.env` 세팅
4. GitHub Secrets(`ATTACKER_EC2_HOST` 등) 등록 후 Push 시 Actions가 SSH로 자동 배포

### 2. Dummy Web (오토스케일링 그룹 - Pull 배포)
1. ECR 리포지토리 `dummy-web` 생성
2. 코드를 `main` 브랜치에 Push하면 GitHub Actions가 ECR에 이미지를 업로드(Push)하고 종료
3. **AWS 시작 템플릿(Launch Template)**의 User Data가 부팅 시 자동으로 최신 이미지를 Pull 받아 실행 (SSH 직접 배포 없음)