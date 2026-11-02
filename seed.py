from sqlalchemy import select

from database import SessionLocal
from models import Post, User

with SessionLocal.begin() as db:
    existing_user = db.scalar(select(User.id).limit(1))
    if existing_user is not None:
        raise RuntimeError("사용자가 이미 있습니다. seed.py는 빈 테이블에서 한 번만 실행하세요.")

    minsu = User(name="민수", age=23)
    jiyeon = User(name="지연", age=19)
    seojun = User(name="서준", age=21)
    db.add_all([
        minsu, jiyeon, seojun,
        Post(title="첫 번째 글", author=minsu),
        Post(title="FastAPI 공부", author=minsu),
        Post(title="SQL 정리", author=jiyeon),
    ])

print("사용자 3명과 게시글 3개를 저장했습니다.")
