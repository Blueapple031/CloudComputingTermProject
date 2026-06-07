"""
시스템·요청 지표 API.

GET /api/metrics — JSON (대시보드 1초 폴링, CloudWatch 대조용)
"""

from fastapi import APIRouter

from app.request_stats import request_stats
from app.system_metrics import get_system_metrics

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """
    CPU 가용량·메모리·요청 통계를 한 번에 반환.

    attacker 부하 테스트 중 이 API 또는 `/` 대시보드를 보면
    cpu_percent 가 올라가고 cpu_available_percent 가 내려가는 것을 확인할 수 있다.
    """
    return {
        "service": "dummy-web",
        **get_system_metrics(),
        "requests": request_stats.to_dict(),
    }
