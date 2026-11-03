# 3단계 · 역할을 나눈 코드

아래 네 파일을 그대로 적용한다. lab 4의 CRUD 동작은 유지하고, 4단계의 게시글 수 제한은 아직 구현하지 않은 상태다. 파일명은 모두 복수형(`repositories.py`, `services.py`, `routers.py`)이다.

`app/database.py`의 `get_db`는 그대로 사용한다. 적용 후 `uv run pytest -q tests/test_start.py validation`으로 기존 CRUD를 확인한다. 예상 결과는 **12 passed**다.

## app/repositories.py

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, User


class PostRepository:
    def __init__(self, db: Annotated[Session, Depends(get_db)]):
        self.db = db

    def get_post(self, post_id: int | None = None):
        if post_id is not None:
            return self.db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
        return self.db.scalars(select(Post).order_by(Post.id)).all()

    def get_user(self, user_id: int):
        return self.db.get(User, user_id)

    def create_post(self, title: str, user_id: int):
        post = Post(title=title, user_id=user_id)
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def update_post(self, post_id: int, title: str):
        post = self.db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
        if post is None:
            return None
        post.title = title
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_post(self, post_id: int):
        post = self.db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
        if post is None:
            return False
        self.db.delete(post)
        self.db.commit()
        return True
```

## app/services.py

```python
from typing import Annotated

from fastapi import Depends, HTTPException

from app.repositories import PostRepository


class PostService:
    def __init__(self, repository: Annotated[PostRepository, Depends()]):
        self.repository = repository

    def get_post(self, post_id: int | None = None):
        return self.repository.get_post(post_id)

    def create_post(self, title: str, user_id: int):
        if self.repository.get_user(user_id) is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return self.repository.create_post(title, user_id)

    def update_post(self, post_id: int, title: str):
        return self.repository.update_post(post_id, title)

    def delete_post(self, post_id: int):
        return self.repository.delete_post(post_id)
```

## app/routers.py

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.schemas import PostCreate, PostResponse, PostUpdate
from app.services import PostService

post_router = APIRouter()


@post_router.get("/posts", response_model=list[PostResponse], tags=["게시글"])
def get_posts(service: Annotated[PostService, Depends(PostService)]):
    return service.get_post()


@post_router.get("/posts/{post_id}", response_model=PostResponse, tags=["게시글"])
def get_post(
    post_id: Annotated[int, Path(gt=0)],
    service: Annotated[PostService, Depends(PostService)],
):
    post = service.get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


@post_router.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["게시글"],
)
def create_post(
    body: PostCreate, service: Annotated[PostService, Depends(PostService)]
):
    return service.create_post(title=body.title, user_id=body.user_id)


@post_router.patch("/posts/{post_id}", response_model=PostResponse, tags=["게시글"])
def update_post(
    post_id: Annotated[int, Path(gt=0)],
    body: PostUpdate,
    service: Annotated[PostService, Depends(PostService)],
):
    post = service.update_post(post_id, body.title)
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


@post_router.delete(
    "/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["게시글"]
)
def delete_post(
    post_id: Annotated[int, Path(gt=0)],
    service: Annotated[PostService, Depends(PostService)],
):
    if not service.delete_post(post_id):
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

## app/main.py

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import post_router

app = FastAPI(title="5주차 실습")

app.include_router(post_router, tags=["Posts"])


@app.get("/health", tags=["연결 확인"])
def health(db: Annotated[Session, Depends(get_db)]):
    db.scalar(select(1))
    return {"status": "ok"}
```
