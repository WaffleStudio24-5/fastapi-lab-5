from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

with SessionLocal() as db:
    users = db.scalars(select(User).order_by(User.id)).all()
    print("사용자 수:", len(users))
    for user in users:
        print(user.id, user.name, user.age, user.nickname)
    if not users:
        raise RuntimeError("4단계의 seed.py를 먼저 실행해 주세요.")
    user = users[0]
    user.nickname = "minsu"
    db.commit()
    db.refresh(user)
    print("저장 후:", user.id, user.name, user.nickname)
