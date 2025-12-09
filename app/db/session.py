# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# from app.core.config import settings


# engine = create_engine(
#     settings.MYSQL_DSN,
#     connect_args={"check_same_thread": False}
#     if settings.MYSQL_DSN.startswith("sqlite")
#     else {},
#     future=True,
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

