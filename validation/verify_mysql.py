"""별도 임시 MySQL에서 시작 코드와 실제 migration을 검증한다."""
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

from sqlalchemy import URL, create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def main():
    name = "lab5-verify-" + uuid4().hex[:10]
    engine = None
    docker(
        "run", "-d", "--rm", "--name", name,
        "-p", "127.0.0.1::3306",
        "-e", "MYSQL_ROOT_PASSWORD=verify-only",
        "-e", "MYSQL_DATABASE=lab5_verify",
        "-e", "MYSQL_USER=seminar",
        "-e", "MYSQL_PASSWORD=verify-only",
        "mysql:8.4",
    )
    try:
        port = int(docker("port", name, "3306/tcp").rsplit(":", 1)[1])
        url = URL.create(
            "mysql+pymysql", username="seminar", password="verify-only",
            host="127.0.0.1", port=port, database="lab5_verify",
            query={"charset": "utf8mb4"},
        )
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        for _ in range(90):
            try:
                with engine.connect() as db:
                    db.execute(text("SELECT 1"))
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("임시 MySQL이 시작되지 않았습니다.")

        env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False))

        def run(*args, success=True):
            result = subprocess.run(
                [sys.executable, *args], cwd=ROOT, env=env,
                capture_output=True, text=True, timeout=60,
            )
            if success and result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            return result

        run("-m", "alembic", "upgrade", "0001")
        with engine.begin() as db:
            db.execute(text("INSERT INTO users (name, age) VALUES ('migration check', 23)"))
        run("-m", "alembic", "upgrade", "head")
        run("-m", "alembic", "check")
        assert "nickname" in {c["name"] for c in inspect(engine).get_columns("users")}
        with engine.begin() as db:
            assert db.scalar(text("SELECT name FROM users")) == "migration check"
            assert db.scalar(text("SELECT nickname FROM users")) is None
            db.execute(text("DELETE FROM users"))
        run("seed.py")
        with engine.connect() as db:
            assert db.scalar(text("SELECT COUNT(*) FROM users")) == 3
            assert db.scalar(text("SELECT COUNT(*) FROM posts")) == 3
        assert run("seed.py", success=False).returncode != 0
        run("nickname.py")
        run("-c", '''
from fastapi.testclient import TestClient
from main import app
with TestClient(app) as client:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    posts = client.get("/posts").json()
    assert len(posts) == 3
    assert [p["id"] for p in posts] == sorted(p["id"] for p in posts)
    response = client.post("/posts", json={"title": "새 글", "user_id": posts[0]["user_id"]})
    assert response.status_code == 201, response.text
    post = response.json()
    path = f"/posts/{post['id']}"
    assert client.get(path).json() == post
    assert client.patch(path, json={"title": "수정"}).status_code == 200
    assert client.get(path).json()["title"] == "수정"
    response = client.delete(path)
    assert response.status_code == 204 and response.content == b""
    assert client.get(path).status_code == 404
    assert client.post("/posts", json={"title": "글", "user_id": 999999}).status_code == 404
    assert client.get("/posts/0").status_code == 422
    assert client.post("/posts", json={"title": " ", "user_id": 1}).status_code == 422
''')
        # 같은 이력을 빈 DB에 다시 적용할 수 있는지 확인한다. 임시 DB만 초기화한다.
        run("-m", "alembic", "downgrade", "base")
        run("-m", "alembic", "upgrade", "head")
        run("-m", "alembic", "check")
        with engine.connect() as db:
            assert db.scalar(text("SELECT COUNT(*) FROM users")) == 0
        print("PASS MySQL: migration·기존 데이터 보존·seed·CRUD·404/422/204·빈 DB 재적용")
    finally:
        if engine is not None:
            engine.dispose()
        docker("stop", name)


if __name__ == "__main__":
    main()
