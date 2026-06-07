"""
호스트(컨테이너/EC2) CPU·메모리 지표 수집.

psutil 로 OS 레벨 사용률을 읽는다.
Docker 컨테이너 안에서도 cgroup 기준으로 컨테이너에 할당된 CPU 대비 % 가 나온다.
EC2 CloudWatch CPUUtilization 과 같은 개념을 웹 UI 에서 바로 확인하기 위함.
"""

from __future__ import annotations

import socket
import time
from typing import Any

import psutil

from app.config import settings

# 앱 기동 시각 — uptime 계산용
_started_at = time.time()

# psutil.cpu_percent(interval=None) 은 첫 호출이 0.0 이라 priming 필요
_psutil_cpu_primed = False


def _prime_cpu_percent() -> None:
    global _psutil_cpu_primed
    if not _psutil_cpu_primed:
        psutil.cpu_percent(interval=None)
        _psutil_cpu_primed = True


def get_system_metrics() -> dict[str, Any]:
    """
    현재 CPU·메모리 스냅샷.

    Returns:
        cpu_percent      : 0~100 (사용 중)
        cpu_available    : 0~100 (여유 = 100 - 사용)
        cpu_count        : 논리 코어 수
        memory_*         : RAM 사용량 (MB, %)
        load_avg_1m      : 1분 load average (Windows 는 None)
    """
    _prime_cpu_percent()
    cpu_used = psutil.cpu_percent(interval=None)
    cpu_used = round(cpu_used, 2)
    cpu_available = round(max(0.0, 100.0 - cpu_used), 2)

    mem = psutil.virtual_memory()
    load_avg = None
    try:
        load_avg = round(psutil.getloadavg()[0], 2)
    except (AttributeError, OSError):
        pass  # Windows 등 load average 미지원

    return {
        "cpu_percent": cpu_used,
        "cpu_available_percent": cpu_available,
        "cpu_count": psutil.cpu_count(logical=True) or 1,
        "memory_total_mb": round(mem.total / (1024 * 1024), 1),
        "memory_used_mb": round(mem.used / (1024 * 1024), 1),
        "memory_available_mb": round(mem.available / (1024 * 1024), 1),
        "memory_percent": round(mem.percent, 2),
        "memory_available_percent": round(max(0.0, 100.0 - mem.percent), 2),
        "load_avg_1m": load_avg,
        "uptime_sec": round(time.time() - _started_at, 1),
        "instance_id": settings.instance_id,
        "hostname": socket.gethostname(),
    }
