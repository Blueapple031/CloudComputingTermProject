"""
attacker-web 환경 설정.

TARGET_URL: 부하를 보낼 대상 (Phase 1: dummy-web EC2, Phase 2: ALB DNS)
ALLOWED_TARGET_HOSTS: 화이트리스트 — 실습 환경 외 URL 공격 방지
MAX_RPS: 안전 상한 (EC2 attacker 자체 과부하 / 비용 방지)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """attacker-web 런타임 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8080

    # Phase 1 로컬 docker-compose 기본값 (dummy-web 서비스명)
    target_url: str = "http://dummy-web:8000/api/load?ms=100"

    # 쉼표 구분 호스트 화이트리스트 (비어 있으면 target_url 호스트만 허용)
    # 예: "dummy-web,10.0.1.50,internal-alb-xxx.ap-northeast-2.elb.amazonaws.com"
    allowed_target_hosts: str = "dummy-web,localhost,127.0.0.1"

    # RPS 상한 — UI/API 모두 이 값을 넘기지 않음
    max_rps: int = 2000

    # aiohttp 동시 커넥션 풀 크기 (RPS 와 별개로 outbound 연결 수 제한)
    max_connections: int = 2000

    # HTTP 요청 타임아웃 (초)
    request_timeout_sec: float = 10.0


settings = Settings()
