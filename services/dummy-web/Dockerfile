# dummy-web Docker 이미지
# EC2 #2 및 Phase 2 ASG Launch Template 에서 사용

FROM python:3.12-slim

WORKDIR /app

# curl: deploy.sh 헬스체크 및 Docker HEALTHCHECK 에 사용
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

# 컨테이너 헬스체크 — orchestrator/compose 가 unhealthy 판정에 사용
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
