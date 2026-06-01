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

## EC2 배포 (요약)

1. ECR 리포지토리 `dummy-web`, `attacker-web` 생성
2. EC2 bootstrap: `bash infra/scripts/bootstrap-ec2.sh dummy` (또는 `attacker`)
3. `/opt/app/<service>/` 에 `deploy/` 파일 + `.env` 배치
4. GitHub Secrets 등록 후 `main` push → Actions 자동 배포

자세한 내용은 [개발계획서.md](./개발계획서.md) 참고.
