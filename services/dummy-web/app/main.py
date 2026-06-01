"""
dummy-web FastAPI 진입점.

EC2 #2 (Dummy Target)에서 실행되는 부하 수신 서버.
"""

import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.config import settings
from app.routes import db_sim, health, load


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 훅.

    시작 시 설정값을 로그로 남겨 EC2 배포 후 설정이 올바른지 확인하기 쉽게 한다.
    """
    print(
        f"[dummy-web] starting on {settings.host}:{settings.port} "
        f"instance_id={settings.instance_id} hostname={socket.gethostname()}"
    )
    yield
    print("[dummy-web] shutdown")


app = FastAPI(
    title="dummy-web",
    description="DDoS 부하 실험용 더미 타깃 서버 (교육 목적)",
    version="0.1.0",
    lifespan=lifespan,
)

# ── 라우터 등록 ──────────────────────────────────────
app.include_router(health.router)
app.include_router(load.router)
app.include_router(db_sim.router)


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    브라우저에서 EC2 #2 상태를 빠르게 확인하는 간단한 HTML 페이지.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="utf-8"><title>dummy-web</title></head>
    <body>
        <h1>dummy-web</h1>
        <p>부하 실험용 더미 타깃 서버 (EC2 #2)</p>
        <ul>
            <li><a href="/health">/health</a> — 헬스체크</li>
            <li><a href="/api/load?ms=100">/api/load?ms=100</a> — CPU 부하</li>
            <li><a href="/api/db-sim?delay_ms=50">/api/db-sim</a> — DB 지연 시뮬</li>
        </ul>
        <p>instance_id: <code>{settings.instance_id}</code></p>
        <p>hostname: <code>{socket.gethostname()}</code></p>
    </body>
    </html>
    """


@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    """
    모든 응답에 인스턴스 식별 헤더 추가.

    Attacker / curl 로 요청 시 어느 dummy 인스턴스가 응답했는지 추적 가능.
    """
    response = await call_next(request)
    response.headers["X-Service"] = "dummy-web"
    response.headers["X-Instance-Id"] = settings.instance_id
    return response
