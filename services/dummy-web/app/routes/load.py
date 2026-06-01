"""
CPU 바운드 부하 엔드포인트.

Attacker EC2가 이 URL을 고빈도로 호출하면 dummy-web EC2 CPU가 상승한다.
실험 E1~E3에서 임계 RPS 측정 시 주로 사용한다.
"""

import socket
import time

from fastapi import APIRouter, Query, Response

from app.config import settings

router = APIRouter(prefix="/api", tags=["load"])


def _cpu_burn(duration_ms: int) -> None:
    """
    지정된 시간 동안 CPU를 소모하는 busy loop.

    sleep()이 아닌 연산 루프를 사용해 CPU Utilization을 올린다.
    CloudWatch CPU 지표가 실제로 반응하도록 하기 위함.

    Args:
        duration_ms: 연산 지속 시간 (밀리초)
    """
    deadline = time.perf_counter() + (duration_ms / 1000.0)
    # 간단한 해시 연산 반복 — sleep 없이 CPU 사용
    value = 0
    while time.perf_counter() < deadline:
        value = (value * 31 + 17) % 1_000_003


@router.get("/load")
async def simulate_load(
    response: Response,
    ms: int = Query(
        default=None,
        ge=1,
        description="CPU 연산 시간(ms). 미지정 시 default_load_ms 사용",
    ),
):
    """
    CPU 바운드 작업 수행 후 응답.

    Query Params:
        ms: 연산 시간 (1 ~ max_load_ms)

    Response Headers:
        X-Instance-Id: 어느 EC2/컨테이너가 처리했는지 (LB 실험 시 유용)
        X-Load-Ms: 실제 적용된 연산 시간
    """
    # ms 파라미터 클램핑 — 악의적 초장시간 요청 방지
    load_ms = ms if ms is not None else settings.default_load_ms
    load_ms = min(max(load_ms, 1), settings.max_load_ms)

    started = time.perf_counter()
    _cpu_burn(load_ms)
    elapsed_ms = (time.perf_counter() - started) * 1000

    # 인스턴스 식별 헤더 — Phase 2 LB 실험에서 어느 타깃이 응답했는지 확인
    response.headers["X-Instance-Id"] = settings.instance_id
    response.headers["X-Hostname"] = socket.gethostname()
    response.headers["X-Load-Ms"] = str(load_ms)

    return {
        "ok": True,
        "requested_ms": load_ms,
        "elapsed_ms": round(elapsed_ms, 2),
        "instance_id": settings.instance_id,
    }
