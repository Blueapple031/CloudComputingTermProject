"""
DB 지연 시뮬레이션 엔드포인트.

/api/load 와 달리 asyncio.sleep 으로 I/O 대기를 모사한다.
CPU 바운드 vs I/O 바운드 부하 패턴 비교 실험에 사용할 수 있다.
"""

import asyncio
import socket
import time

from fastapi import APIRouter, Query, Response

from app.config import settings

router = APIRouter(prefix="/api", tags=["db-sim"])


@router.get("/db-sim")
async def simulate_db_query(
    response: Response,
    delay_ms: int = Query(
        default=None,
        ge=1,
        description="인위적 DB 지연(ms). 미지정 시 default_db_delay_ms",
    ),
):
    """
    비동기 sleep으로 DB 쿼리 지연을 흉내 낸다.

    CPU는 상대적으로 낮고, 동시 요청 수가 많으면 이벤트 루프/커넥션 부하가 증가한다.
    """
    delay = delay_ms if delay_ms is not None else settings.default_db_delay_ms
    delay = min(max(delay, 1), settings.max_db_delay_ms)

    started = time.perf_counter()
    # asyncio.sleep: 스레드 블로킹 없이 I/O 대기 시뮬레이션
    await asyncio.sleep(delay / 1000.0)
    elapsed_ms = (time.perf_counter() - started) * 1000

    response.headers["X-Instance-Id"] = settings.instance_id
    response.headers["X-Hostname"] = socket.gethostname()
    response.headers["X-Db-Delay-Ms"] = str(delay)

    return {
        "ok": True,
        "requested_delay_ms": delay,
        "elapsed_ms": round(elapsed_ms, 2),
        "instance_id": settings.instance_id,
    }
