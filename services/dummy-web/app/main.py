"""
dummy-web FastAPI 진입점.

EC2 #2 (Dummy Target)에서 실행되는 부하 수신 서버.
/ 대시보드에서 CPU 가용량을 실시간 확인할 수 있다.
"""

import socket
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.request_stats import request_stats
from app.routes import db_sim, health, load, metrics
from app.system_metrics import _prime_cpu_percent

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """시작 시 CPU 측정 priming — 첫 /api/metrics 값이 0으로 나오는 것 방지."""
    _prime_cpu_percent()
    print(
        f"[dummy-web] starting on {settings.host}:{settings.port} "
        f"instance_id={settings.instance_id} hostname={socket.gethostname()}"
    )
    yield
    print("[dummy-web] shutdown")


app = FastAPI(
    title="dummy-web",
    description="DDoS 부하 실험용 더미 타깃 서버 (교육 목적)",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(load.router)
app.include_router(db_sim.router)
app.include_router(metrics.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """CPU·메모리 실시간 대시보드 (1초 자동 갱신)."""
    return templates.TemplateResponse(request, "index.html", {})


@app.middleware("http")
async def track_requests_and_headers(request: Request, call_next):
    """
    요청 통계 집계 + 인스턴스 식별 헤더.

    /api/metrics 폴링은 other_requests 에 포함되지만 부하 테스트 시
    /api/load 비중이 압도적으로 커서 CPU 상승과 함께 load 카운터가 잘 보인다.
    """
    # metrics API 자체는 통계에서 제외 (폴링 노이즈 감소)
    if not request.url.path.startswith("/api/metrics"):
        request_stats.record(request.url.path)

    response = await call_next(request)
    response.headers["X-Service"] = "dummy-web"
    response.headers["X-Instance-Id"] = settings.instance_id
    return response
