"""
환경 변수 및 애플리케이션 설정.

Docker / docker-compose / EC2 모두 동일한 환경변수 이름을 사용한다.
로컬: deploy/docker-compose.yml 의 environment 섹션
EC2: /opt/app/dummy-web/.env 또는 docker-compose.prod.yml
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """dummy-web 런타임 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 서버 바인딩 (Dockerfile EXPOSE와 맞출 것)
    host: str = "0.0.0.0"
    port: int = 8000

    # 응답 헤더에 포함할 인스턴스 식별자 (EC2 metadata 또는 hostname)
    # CloudWatch / ALB 실험 시 어느 인스턴스가 요청을 처리했는지 구분용
    instance_id: str = "local-dev"

    # /api/load 기본 CPU 연산 시간 (밀리초)
    default_load_ms: int = 100

    # /api/load 에서 허용하는 최대 연산 시간 (과도한 부하 방지)
    max_load_ms: int = 5000

    # /api/db-sim 기본 지연 (밀리초)
    default_db_delay_ms: int = 50

    # /api/db-sim 최대 지연
    max_db_delay_ms: int = 3000


# 전역 설정 싱글톤 — FastAPI lifespan / 라우터에서 import
settings = Settings()
