"""
라우트 모듈 패키지.

각 파일은 하나의 API 그룹을 담당한다.
- health.py : 헬스체크 (ALB Target Group, Docker healthcheck)
- load.py   : CPU 바운드 부하 (DDoS 실험 핵심 엔드포인트)
- db_sim.py : I/O 대기 시뮬레이션 (DB 쿼리 지연 모사)
"""
