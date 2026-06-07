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

## EC2 배포 (Ubuntu)

**추천 — git pull (ECR 없음):** [docs/EC2-git-pull-배포.md](./docs/EC2-git-pull-배포.md)

| 순서 | 문서 |
|------|------|
| 1 | [docs/EC2-Dummy-설정.md](./docs/EC2-Dummy-설정.md) |
| 2 | [docs/EC2-Attacker-설정.md](./docs/EC2-Attacker-설정.md) |
