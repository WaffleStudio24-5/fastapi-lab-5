from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import settings

Engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(
    bind=Engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()

def get_db():
    with SessionLocal() as db:
        yield db
