import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Engine = create_engine(os.environ["DATABASE_URL"], echo=True)
SessionLocal = sessionmaker(
    bind=Engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()
