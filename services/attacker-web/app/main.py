"""
attacker-web FastAPI 진입점 + 실험 제어 UI.

EC2 #1 에서 실행. 웹 UI 또는 REST API 로 부하 테스트를 시작/중지한다.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.load_generator import load_generator
from app.schemas import LoadStatsResponse, StartLoadRequest

# HTML 템플릿 디렉터리
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 종료 시 실행 중인 부하 테스트를 정리한다."""
    print(
        f"[attacker-web] starting on {settings.host}:{settings.port} "
        f"default_target={settings.target_url}"
    )
    yield
    if load_generator.stats.is_running:
        await load_generator.stop()
    print("[attacker-web] shutdown")


app = FastAPI(
    title="attacker-web",
    description="DDoS 부하 실험용 트래픽 생성기 (교육 목적, 화이트리스트 URL만)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Docker / ALB 헬스체크."""
    return {
        "status": "ok",
        "service": "attacker-web",
        "load_running": load_generator.stats.is_running,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    실험 제어 웹 UI.

    JavaScript fetch 로 /api/load/* 호출 — 새로고침 없이 상태 갱신.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "default_target_url": settings.target_url,
            "max_rps": settings.max_rps,
            "stats": load_generator.stats.to_dict(),
        },
    )


@app.get("/api/load/status", response_model=LoadStatsResponse)
async def get_load_status():
    """현재 부하 테스트 통계 (UI 폴링용)."""
    return load_generator.stats.to_dict()


@app.post("/api/load/start", response_model=LoadStatsResponse)
async def start_load(body: StartLoadRequest):
    """
    부하 생성 시작.

    target_url 미지정 시 settings.target_url (환경변수 TARGET_URL) 사용.
    """
    target = body.target_url or settings.target_url
    try:
        stats = await load_generator.start(
            target_url=target,
            rps=body.rps,
            duration_sec=body.duration_sec,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return stats.to_dict()


@app.post("/api/load/stop", response_model=LoadStatsResponse)
async def stop_load():
    """부하 생성 중지."""
    stats = await load_generator.stop()
    return stats.to_dict()
