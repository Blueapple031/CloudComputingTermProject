# EC2 #1 — attacker-web 설정 메뉴얼

> **이 서버 역할:** 부하를 **보내는** 공격(실험) 제어 서버 (포트 8080)  
> **OS 가정:** Ubuntu EC2 (처음 켠 직후)  
> **사용자:** `ubuntu`  
> **선행 조건:** **[Dummy EC2 설정 완료](./EC2-Dummy-설정.md)** + Dummy **Private IP** 확보

---

## ⭐ 가장 쉬운 방법 — git pull (ECR 불필요)

전체: **[EC2-git-pull-배포.md](./EC2-git-pull-배포.md)**

```bash
git clone -b 2026-06-01-thze https://github.com/Blueapple031/CloudComputingTermProject.git
cd CloudComputingTermProject/services/attacker-web
DUMMY_PRIVATE_IP=172.31.33.104 bash deploy/git-deploy.sh
```

`172.31.33.104` → Dummy Private IP 로 변경.

---

## (대안) ECR에서 pull — IAM Role 필요

로컬 PC에서 attacker 이미지를 ECR에 올린다.

```powershell
$REGION = "ap-northeast-2"
$ACCOUNT = "123456789012"          # ← 본인 계정 ID
$ECR = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR

docker build -t "${ECR}/attacker-web:latest" services/attacker-web
docker push "${ECR}/attacker-web:latest"
```

---

## 1. AWS 콘솔 — Attacker EC2 / Security Group

### EC2 생성 시

| 항목 | 값 |
|------|-----|
| 이름 | `attacker` |
| AMI | **Ubuntu** 22.04 / 24.04 |
| 타입 | t3.small |
| VPC | **Dummy EC2 와 같은 VPC** |
| Public IP | 활성화 |

### Security Group (인바운드)

| 포트 | 프로토콜 | 소스 | 용도 |
|------|----------|------|------|
| **22** | TCP | **내 IP** | SSH |
| **8080** | TCP | **내 IP** | attacker 웹 UI |

### Security Group (아웃바운드)

| 포트 | 대상 | 용도 |
|------|------|------|
| **8000** | Dummy **Private IP** / SG | 부하 HTTP 전송 |
| 전체 | 0.0.0.0/0 | ECR pull 등 (기본 허용이면 OK) |

### 미리 적어 둘 것

| 항목 | 예시 | 어디서 |
|------|------|--------|
| Dummy **Private IP** | `172.31.33.104` | Dummy EC2 콘솔 |
| Attacker **Public IP** | `3.36.x.x` | 브라우저 UI 접속 |

---

## 2. SSH 접속

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@<ATTACKER_PUBLIC_IP>
```

---

## 3. 필수 패키지 설치 (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y docker.io curl unzip git docker-compose-v2 awscli

sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

**SSH 끊었다가 다시 접속**

```bash
docker ps
```

---

## 4. ECR에서 이미지 받기

```bash
export AWS_REGION=ap-northeast-2
export ECR_REGISTRY=123456789012.dkr.ecr.ap-northeast-2.amazonaws.com

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

docker pull $ECR_REGISTRY/attacker-web:latest
```

---

## 5. attacker-web 컨테이너 실행

**`DUMMY_PRIVATE_IP` 를 Dummy EC2 Private IP 로 바꾼다.**

```bash
export DUMMY_PRIVATE_IP=172.31.33.104   # ← 실제 값으로 변경

docker run -d \
  --name attacker-web \
  --restart unless-stopped \
  -p 8080:8080 \
  -e TARGET_URL=http://${DUMMY_PRIVATE_IP}:8000/api/load?ms=100 \
  -e ALLOWED_TARGET_HOSTS=${DUMMY_PRIVATE_IP} \
  -e MAX_RPS=5000 \
  $ECR_REGISTRY/attacker-web:latest
```

| 환경변수 | 의미 |
|----------|------|
| `TARGET_URL` | 부하를 보낼 Dummy 주소 |
| `ALLOWED_TARGET_HOSTS` | 이 IP 외 URL은 차단 (실습 안전) |
| `MAX_RPS` | 초당 요청 상한 |

다시 실행할 때:

```bash
docker rm -f attacker-web
# 위 docker run 다시
```

---

## 6. Dummy 연결 테스트 (Attacker EC2 안에서)

```bash
curl http://${DUMMY_PRIVATE_IP}:8000/health
```

여기서 실패하면 **Security Group** 문제다 (Attacker → Dummy 8000).

```bash
curl http://localhost:8080/health
```

attacker 자체는 이걸로 확인.

---

## 7. 브라우저에서 실험

내 PC에서:

```text
http://<ATTACKER_PUBLIC_IP>:8080
```

1. 대상 URL이 `http://<Dummy Private IP>:8000/api/load?ms=100` 인지 확인  
2. RPS `100` 정도로 **시작**  
3. Dummy 대시보드 `http://<DUMMY_PUBLIC_IP>:8000` 에서 **CPU % 상승** 확인

---

## 8. 자주 나는 문제

| 증상 | 해결 |
|------|------|
| 시작 시 400 / 허용되지 않은 호스트 | `ALLOWED_TARGET_HOSTS` 에 Dummy Private IP 포함 |
| 부하 시작해도 Dummy CPU 안 오름 | `TARGET_URL` 이 Private IP 인지, Dummy 8000 열렸는지 |
| Attacker UI 안 열림 | SG 인바운드 8080 + **내 IP** |
| Dummy에 curl 실패 | Dummy SG: 8000 ← Attacker SG 또는 Attacker IP |
| Public IP를 TARGET_URL에 넣음 | 같은 VPC면 **Private IP** 사용 권장 |

---

## 9. 컨테이너 관리 명령

```bash
docker ps                          # 실행 중인지
docker logs attacker-web --tail 30 # 로그
docker stop attacker-web           # 중지
docker start attacker-web          # 재시작
```

---

## 한 줄 요약

```text
apt로 docker 설치 → ECR pull → Dummy Private IP 넣어서 docker run -p 8080:8080 → :8080 UI
```

---

## 전체 순서 (처음부터)

1. [Dummy EC2 설정](./EC2-Dummy-설정.md) 먼저  
2. Dummy Private IP 메모  
3. **이 문서**대로 Attacker EC2 설정  
4. Attacker UI에서 부하 시작 → Dummy CPU 확인
