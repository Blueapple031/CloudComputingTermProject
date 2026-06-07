# EC2 배포 — git pull 방식 (가장 쉬움)

> **ECR, IAM Role, aws configure 전부 불필요**  
> EC2에서 레포 받아서 `docker build` → `docker run` 만 한다.

| EC2 | 문서 섹션 |
|-----|-----------|
| Dummy (#2) | [1. Dummy](#1-dummy-ec2) |
| Attacker (#1) | [2. Attacker](#2-attacker-ec2) |

레포: `https://github.com/Blueapple031/CloudComputingTermProject.git`  
브랜치: `2026-06-01-thze` (바뀌면 스크립트 `BRANCH=` 수정)

---

## 공통 — Ubuntu EC2 처음 1회

```bash
sudo apt-get update
sudo apt-get install -y docker.io git curl

sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

**SSH 끊고 다시 접속** 후 `docker ps` 확인.

---

## 1. Dummy EC2

```bash
git clone -b 2026-06-01-thze \
  https://github.com/Blueapple031/CloudComputingTermProject.git

cd CloudComputingTermProject/services/dummy-web
bash deploy/git-deploy.sh
```

### 코드 수정 후 다시 배포

```bash
cd ~/CloudComputingTermProject
git pull
cd services/dummy-web
bash deploy/git-deploy.sh
```

### 확인

- EC2: `curl http://localhost:8000/health`
- 브라우저: `http://<DUMMY_PUBLIC_IP>:8000`

### Private IP 확인 (Attacker에 필요)

```bash
hostname -I | awk '{print $1}'
```

---

## 2. Attacker EC2

Dummy **Private IP** 를 알고 나서:

```bash
git clone -b 2026-06-01-thze \
  https://github.com/Blueapple031/CloudComputingTermProject.git

cd CloudComputingTermProject/services/attacker-web
DUMMY_PRIVATE_IP=172.31.33.104 bash deploy/git-deploy.sh
```

`172.31.33.104` → 실제 Dummy Private IP 로 변경.

### 다시 배포

```bash
cd ~/CloudComputingTermProject
git pull
cd services/attacker-web
DUMMY_PRIVATE_IP=172.31.33.104 bash deploy/git-deploy.sh
```

### 확인

- `curl http://<DUMMY_PRIVATE_IP>:8000/health` (Attacker EC2에서)
- 브라우저: `http://<ATTACKER_PUBLIC_IP>:8080`

---

## Security Group (그대로 필요)

| 서버 | 포트 | 누구 |
|------|------|------|
| Dummy | 8000 | Attacker EC2 |
| Dummy | 22 | 내 IP |
| Attacker | 8080 | 내 IP |
| Attacker | 22 | 내 IP |

---

## 수동으로 하고 싶을 때 (스크립트 없이)

**Dummy:**

```bash
cd ~/CloudComputingTermProject/services/dummy-web
docker build -t dummy-web:latest .
docker rm -f dummy-web 2>/dev/null || true
docker run -d --name dummy-web --restart unless-stopped \
  -p 8000:8000 -e INSTANCE_ID=dummy-ec2 dummy-web:latest
```

**Attacker:**

```bash
cd ~/CloudComputingTermProject/services/attacker-web
docker build -t attacker-web:latest .
docker rm -f attacker-web 2>/dev/null || true
docker run -d --name attacker-web --restart unless-stopped \
  -p 8080:8080 \
  -e TARGET_URL=http://<DUMMY_PRIVATE_IP>:8000/api/load?ms=100 \
  -e ALLOWED_TARGET_HOSTS=<DUMMY_PRIVATE_IP> \
  attacker-web:latest
```

---

## 비교

| 방식 | 난이도 | 필요한 것 |
|------|--------|-----------|
| **git pull + build** | 쉬움 | git, docker |
| ECR pull | 보통 | IAM Role, ECR push |
| docker save/scp | 보통 | 로컬 docker, scp |

---

## 한 줄 요약

```text
git clone → bash deploy/git-deploy.sh  (Dummy 먼저, Attacker는 DUMMY_PRIVATE_IP=)
```
