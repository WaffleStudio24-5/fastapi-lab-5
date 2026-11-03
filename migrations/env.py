from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401 — Alembic에 모델을 등록한다.
from app.database import Base
from app.settings import settings

url = settings.database_url

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
