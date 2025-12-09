# from sqlalchemy import create_engine, text
# from sqlalchemy.engine import Engine
# from app.core.config import settings

# _engine: Engine | None = None

# def get_engine() -> Engine:
#     global _engine
#     if _engine is None:
#         _engine = create_engine(settings.MYSQL_DSN, pool_pre_ping=True, pool_recycle=1800)
#     return _engine

# def run_select(sql: str) -> list[dict]:
#     eng = get_engine()
#     with eng.connect() as conn:
#         result = conn.execution_options(timeout=settings.SQL_TIMEOUT_SECONDS).execute(text(sql))
#         return [dict(r._mapping) for r in result]
     