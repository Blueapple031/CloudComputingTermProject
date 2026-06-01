"""
헬스체크 엔드포인트.

ALB Target Group, Docker HEALTHCHECK, GitHub Actions deploy.sh 가
이 URL을 호출해 서비스 기동 여부를 확인한다.
"""

import socket
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    가벼운 헬스체크 — CPU 부하 없음.

    Returns:
        status, instance_id, hostname, timestamp
    """
    return {
        "status": "ok",
        "service": "dummy-web",
        "instance_id": settings.instance_id,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
