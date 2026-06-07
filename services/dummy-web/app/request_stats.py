"""
요청 통계 — 대시보드에서 부하 영향 확인용.

middleware 에서 increment 하며, /api/load 호출이 늘면 total_requests 도 함께 증가한다.
"""

from dataclasses import dataclass, field
import time


@dataclass
class RequestStats:
    """누적 HTTP 요청 카운터."""

    total: int = 0
    api_load: int = 0
    api_db_sim: int = 0
    other: int = 0
    started_at: float = field(default_factory=time.time)

    def record(self, path: str) -> None:
        self.total += 1
        if path.startswith("/api/load"):
            self.api_load += 1
        elif path.startswith("/api/db-sim"):
            self.api_db_sim += 1
        else:
            self.other += 1

    def to_dict(self) -> dict:
        elapsed = max(time.time() - self.started_at, 0.001)
        return {
            "total_requests": self.total,
            "api_load_requests": self.api_load,
            "api_db_sim_requests": self.api_db_sim,
            "other_requests": self.other,
            "avg_rps_since_boot": round(self.total / elapsed, 2),
        }


# 전역 싱글톤 — middleware / metrics API 에서 공유
request_stats = RequestStats()
