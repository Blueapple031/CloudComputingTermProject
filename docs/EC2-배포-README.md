# EC2 배포 — 어떤 문서를 보나?

| 순서 | 문서 | 대상 EC2 |
|------|------|----------|
| **추천** | **[EC2-git-pull-배포.md](./EC2-git-pull-배포.md)** | git pull + docker build (ECR 없음) |
| 1 | **[EC2-Dummy-설정.md](./EC2-Dummy-설정.md)** | EC2 #2 — dummy-web |
| 2 | **[EC2-Attacker-설정.md](./EC2-Attacker-설정.md)** | EC2 #1 — attacker-web |

- **OS:** Ubuntu (`ubuntu` 사용자, `apt` 사용)
- **가장 쉬움:** `git clone` → `bash deploy/git-deploy.sh`
- **상세·CI/CD:** [EC2-배포가이드.md](./EC2-배포가이드.md)
