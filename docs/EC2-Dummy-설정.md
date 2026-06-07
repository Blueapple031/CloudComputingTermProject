# EC2 #2 — dummy-web 설정 메뉴얼

> **이 서버 역할:** 부하를 **받는** 타깃 서버 (포트 8000)  
> **OS 가정:** Ubuntu EC2 (처음 켠 직후, 아무것도 설치 안 된 상태)  
> **사용자:** `ubuntu` (Amazon Linux 의 `ec2-user` 아님)

---

## ⭐ 가장 쉬운 방법 — git pull (ECR 불필요)

전체: **[EC2-git-pull-배포.md](./EC2-git-pull-배포.md)**

```bash
# Docker + git 설치 후 (아래 3절)
git clone -b 2026-06-01-thze https://github.com/Blueapple031/CloudComputingTermProject.git
cd CloudComputingTermProject/services/dummy-web
bash deploy/git-deploy.sh
```

코드 업데이트: `cd ~/CloudComputingTermProject && git pull` 후 `bash deploy/git-deploy.sh` 다시.

---

## (대안) ECR에서 pull — IAM Role 필요

로컬 PC에서 Docker 이미지를 ECR에 올려 두어야 EC2에서 받을 수 있다.

```powershell
# 로컬 PowerShell — 프로젝트 폴더에서
$REGION = "ap-northeast-2"
$ACCOUNT = "123456789012"          # ← 본인 AWS 계정 ID
$ECR = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR

docker build -t "${ECR}/dummy-web:latest" services/dummy-web
docker push "${ECR}/dummy-web:latest"
```

ECR에 `dummy-web` 리포지토리가 없으면 AWS 콘솔에서 먼저 만든다.

---

## 1. AWS 콘솔 — Dummy EC2 / Security Group

### EC2 생성 시

| 항목 | 값 |
|------|-----|
| 이름 | `dummy` (아무거나) |
| AMI | **Ubuntu** 22.04 / 24.04 |
| 타입 | t3.small 또는 t3.micro |
| 키 페어 | `.pem` 파일 받아서 보관 |
| Public IP | 활성화 |

### Security Group (인바운드)

| 포트 | 프로토콜 | 소스 | 용도 |
|------|----------|------|------|
| **22** | TCP | **내 IP** | SSH |
| **8000** | TCP | **Attacker EC2 SG** 또는 Attacker Private IP | dummy-web |

> 8000은 인터넷 전체(0.0.0.0/0)에 열지 말 것. Attacker EC2만 접근하게.

### 메모해 둘 것

- **Public IP** — 브라우저 접속·SSH용 (예: `3.35.x.x`)
- **Private IP** — Attacker 설정에 필요 (예: `172.31.33.104`)

---

## 2. SSH 접속

```powershell
# Windows PowerShell
ssh -i "C:\path\to\your-key.pem" ubuntu@<DUMMY_PUBLIC_IP>
```

처음 접속 시 `ubuntu@ip-172-31-xx-xx` 프롬프트가 보이면 성공.

---

## 3. 필수 패키지 설치 (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y docker.io curl unzip git

# Docker Compose (v2)
sudo apt-get install -y docker-compose-v2

# ECR pull 용 (선택 — 아래 aws 명령 쓸 때 필요)
sudo apt-get install -y awscli

sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

**반드시 SSH 끊었다가 다시 접속** (docker 권한 적용)

```bash
exit
```

다시 `ssh -i ... ubuntu@<DUMMY_PUBLIC_IP>` 접속 후:

```bash
docker ps
```

에러 없이 표만 나오면 OK.

---

## 4. ECR에서 이미지 받기

아래 `123456789012` 를 **본인 계정 ID**로 바꾼다.

```bash
export AWS_REGION=ap-northeast-2
export ECR_REGISTRY=123456789012.dkr.ecr.ap-northeast-2.amazonaws.com

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

docker pull $ECR_REGISTRY/dummy-web:latest
```

### `aws: command not found` 나올 때

```bash
sudo apt-get install -y awscli
```

### ECR 로그인 실패 시

EC2에 IAM Role `AmazonEC2ContainerRegistryReadOnly` 붙이거나, `aws configure` 로 키 설정.

---

## 5. dummy-web 컨테이너 실행

```bash
docker run -d \
  --name dummy-web \
  --restart unless-stopped \
  -p 8000:8000 \
  -e INSTANCE_ID=dummy-ec2-1 \
  $ECR_REGISTRY/dummy-web:latest
```

| 옵션 | 의미 |
|------|------|
| `-p 8000:8000` | 외부 8000 → 컨테이너 8000 |
| `-e INSTANCE_ID=...` | 대시보드에 표시되는 서버 이름 |

이미 한 번 실행했으면:

```bash
docker rm -f dummy-web   # 기존 삭제 후 다시 run
```

---

## 6. 동작 확인

### EC2 안에서

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/metrics
docker ps
docker logs dummy-web --tail 20
```

`{"status":"ok",...}` 나오면 성공.

### 내 PC 브라우저

```text
http://<DUMMY_PUBLIC_IP>:8000
```

CPU·메모리 대시보드가 보이면 완료.

---

## 7. 자주 나는 문제

| 증상 | 해결 |
|------|------|
| `dnf: command not found` | Ubuntu → `apt-get` 사용 (이 메뉴얼 따르기) |
| `ec2-user does not exist` | Ubuntu → 사용자는 `ubuntu` |
| `permission denied` (docker) | SSH 재접속 또는 `sudo docker ...` |
| 브라우저 접속 안 됨 | SG 인바운드 8000, 내 IP 또는 Attacker만 허용했는지 확인 |
| ECR pull 실패 | IAM Role / `aws configure` / 리포지토리 이름 `dummy-web` |

---

## 8. Dummy 설정 끝 — 다음

Attacker EC2 설정: **[EC2-Attacker-설정.md](./EC2-Attacker-설정.md)**

Attacker 쪽 `.env` 에 넣을 **Dummy Private IP** 를 이 서버에서 확인:

```bash
hostname -I | awk '{print $1}'
# 또는
ip -4 addr show eth0
```

---

## 한 줄 요약

```text
apt로 docker 설치 → ECR pull → docker run -p 8000:8000 → 브라우저 :8000
```
