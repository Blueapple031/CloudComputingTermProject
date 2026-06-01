"""
API 요청/응답 스키마 (Pydantic).

FastAPI 가 JSON body 검증 및 OpenAPI 문서 생성에 사용한다.
"""

from typing import Optional

from pydantic import BaseModel, Field


class StartLoadRequest(BaseModel):
    """POST /api/load/start 요청 body."""

    target_url: Optional[str] = Field(
        default=None,
        description="부하 대상 URL. 미지정 시 환경변수 TARGET_URL",
    )
    rps: int = Field(default=100, ge=1, le=5000, description="초당 요청 수")
    duration_sec: Optional[int] = Field(
        default=None,
        ge=1,
        description="자동 종료 시간(초). None 이면 수동 stop",
    )


class LoadStatsResponse(BaseModel):
    """부하 테스트 상태 응답."""

    is_running: bool
    target_rps: int
    target_url: str
    total_requests: int
    success_count: int
    error_count: int
    avg_rps: float
    current_rps: float
    avg_latency_ms: float
    elapsed_sec: float
