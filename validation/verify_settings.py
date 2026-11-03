"""임시 폴더에서 설정 우선순위와 앱·Alembic의 연결 일치를 확인한다."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = {key: value for key, value in os.environ.items()
           if key.lower() != "database_url"}
    env["PYTHONPATH"] = str(ROOT)
    with tempfile.TemporaryDirectory(prefix="lab5-settings-") as directory:
        cwd = Path(directory)

        def run(*args, overrides=None):
            return subprocess.run(
                [sys.executable, *args], cwd=cwd,
                env=env | (overrides or {}), capture_output=True, text=True,
                timeout=60,
            )

        missing = run("-c", "from app.settings import settings")
        assert missing.returncode != 0 and "Field required" in missing.stderr
        url = "sqlite+pysqlite:///settings-check.db"
        (cwd / ".env").write_text(f"DATABASE_URL={url}\n", encoding="utf-8")
        result = run("-c", "from app.database import Engine; "
                     f"assert str(Engine.url) == {url!r}")
        assert result.returncode == 0, result.stderr
        override = run("-c", "from app.database import Engine; "
                       "assert str(Engine.url) == 'sqlite+pysqlite:///:memory:'",
                       overrides={"DATABASE_URL": "sqlite+pysqlite:///:memory:"})
        assert override.returncode == 0, override.stderr
        migration = run("-m", "alembic", "-c", str(ROOT / "alembic.ini"),
                        "upgrade", "head")
        assert migration.returncode == 0, migration.stdout + migration.stderr
        check = run("-c", "from app.database import Engine; "
                    "from sqlalchemy import inspect; "
                    "assert {'users', 'posts', 'alembic_version'} <= "
                    "set(inspect(Engine).get_table_names())")
        assert check.returncode == 0, check.stderr
        # 개발용 주소가 잘못되어 있어도 fixture는 테스트 DB로 교체한다.
        (cwd / ".env").write_text("DATABASE_URL=not-a-database-url\n", encoding="utf-8")
        tests = run("-m", "pytest", "-q", str(ROOT / "tests/test_start.py"))
        assert tests.returncode == 0, tests.stdout + tests.stderr
    print("PASS 설정: 필수값·.env·환경 변수 우선·Alembic·테스트 DB 분리")


if __name__ == "__main__":
    main()
