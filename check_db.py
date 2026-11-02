from sqlalchemy import func, inspect, select

from database import Engine

with Engine.connect() as connection:
    print("연결 대상:", Engine.url.host, Engine.url.database)
    print("연결 성공:", connection.scalar(select(func.database())))
    inspector = inspect(connection)
    tables = inspector.get_table_names()
    print("테이블:", ", ".join(tables) or "(없음)")
    for table in ("users", "posts"):
        if table in tables:
            print(table, "열:", ", ".join(c["name"] for c in inspector.get_columns(table)))
