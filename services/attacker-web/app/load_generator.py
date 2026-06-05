"""
부하 생성기 (Load Generator).

asyncio + aiohttp 로 지정 RPS 만큼 대상 URL 에 HTTP GET 요청을 보낸다.
별도 스레드/프로세스 없이 단일 이벤트 루프에서 동작한다.

실험 시나리오:
  - 고정 RPS (E1 베이스라인)
  - Step RPS 변경 (E3)
  - ramp-up/down (추후 확장)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import aiohttp

from app.config import settings


@dataclass
class LoadStats:
    """부하 테스트 진행 중 누적 통계."""

    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    target_rps: int = 0
    target_url: str = ""
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    is_running: bool = False
    # 최근 1초 윈도우 요청 수 (현재 RPS 추정)
    recent_timestamps: list[float] = field(default_factory=list)

    @property
    def elapsed_sec(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.stopped_at or time.time()
        return max(end - self.started_at, 0.001)

    @property
    def avg_rps(self) -> float:
        if self.total_requests == 0 or self.started_at is None:
            return 0.0
        return self.total_requests / self.elapsed_sec

    @property
    def avg_latency_ms(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count

    @property
    def current_rps(self) -> float:
        """최근 1초 동안 완료된 요청 수."""
        now = time.time()
        self.recent_timestamps = [t for t in self.recent_timestamps if now - t <= 1.0]
        return float(len(self.recent_timestamps))

    def to_dict(self) -> dict:
        return {
            "is_running": self.is_running,
            "target_rps": self.target_rps,
            "target_url": self.target_url,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_rps": round(self.avg_rps, 2),
            "current_rps": round(self.current_rps, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "elapsed_sec": round(self.elapsed_sec, 2),
        }


class LoadGenerator:
    """
    비동기 HTTP 부하 생성기 (싱글톤 패턴).

    FastAPI lifespan 에서 start/stop 하며, API/UI 가 상태를 조회한다.
    """

    def __init__(self) -> None:
        self.stats = LoadStats()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._session: Optional[aiohttp.ClientSession] = None

    def _validate_target_url(self, url: str) -> None:
        """
        대상 URL 화이트리스트 검증.

        교육용 실습 환경 외 임의 URL 로의 트래픽 생성을 막는다.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("target_url 은 http 또는 https 여야 합니다.")
        if not parsed.hostname:
            raise ValueError("target_url 에 hostname 이 필요합니다.")

        allowed = {
            h.strip().lower()
            for h in settings.allowed_target_hosts.split(",")
            if h.strip()
        }
        hostname = parsed.hostname.lower()
        if allowed and hostname not in allowed:
            raise ValueError(
                f"허용되지 않은 대상 호스트: {hostname}. "
                f"allowed_target_hosts={settings.allowed_target_hosts}"
            )

    async def start(self, target_url: str, rps: int, duration_sec: Optional[int] = None) -> LoadStats:
        """
        부하 생성 시작.

        Args:
            target_url: HTTP GET 대상 (dummy-web /api/load 등)
            rps: 초당 요청 수 (1 ~ max_rps)
            duration_sec: None 이면 수동 stop 까지, 값 있으면 자동 종료
        """
        if self.stats.is_running:
            raise RuntimeError("이미 부하 테스트가 실행 중입니다.")

        self._validate_target_url(target_url)
        rps = max(1, min(rps, settings.max_rps))

        self._stop_event.clear()
        self.stats = LoadStats(
            started_at=time.time(),
            target_rps=rps,
            target_url=target_url,
            is_running=True,
        )

        # aiohttp 세션 — 커넥션 풀 재사용으로 고 RPS 에 유리
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout_sec)
        # TCP 임시 포트 고갈 방지를 위해 keepalive_timeout 30초 명시적 연장
        connector = aiohttp.TCPConnector(limit=settings.max_connections, keepalive_timeout=30)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)

        self._task = asyncio.create_task(self._run_loop(rps, duration_sec))
        return self.stats

    async def stop(self) -> LoadStats:
        """부하 생성 중지 및 통계 확정."""
        if not self.stats.is_running:
            return self.stats

        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
        if self._session and not self._session.closed:
            await self._session.close()

        self.stats.is_running = False
        self.stats.stopped_at = time.time()
        self._task = None
        self._session = None
        return self.stats

    async def _run_loop(self, rps: int, duration_sec: Optional[int]) -> None:
        """
        RPS 유지 루프.

        interval = 1/rps 초마다 요청 1건 스케줄.
        고 RPS 에서는 asyncio.create_task 로 fire-and-forget (통계만 집계).
        """
        interval = 1.0 / rps
        deadline = time.time() + duration_sec if duration_sec else None

        try:
            while not self._stop_event.is_set():
                if deadline and time.time() >= deadline:
                    break
                # 요청을 await 하지 않고 태스크로 던져 throughput 확보
                asyncio.create_task(self._send_one_request())
                await asyncio.sleep(interval)
        finally:
            self.stats.is_running = False
            self.stats.stopped_at = time.time()
            if self._session and not self._session.closed:
                await self._session.close()

    async def _send_one_request(self) -> None:
        """단일 HTTP GET 요청 + 통계 업데이트."""
        if not self._session:
            return

        self.stats.total_requests += 1
        started = time.perf_counter()
        try:
            async with self._session.get(self.stats.target_url) as resp:
                await resp.read()  # body 소비 (커넥션 반환)
                if 200 <= resp.status < 400:
                    self.stats.success_count += 1
                    latency_ms = (time.perf_counter() - started) * 1000
                    self.stats.total_latency_ms += latency_ms
                else:
                    self.stats.error_count += 1
        except Exception:
            self.stats.error_count += 1

        self.stats.recent_timestamps.append(time.time())


# FastAPI 라우터에서 공유하는 전역 인스턴스
load_generator = LoadGenerator()
