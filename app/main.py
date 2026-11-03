from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Post, User
from app.schemas import PostCreate, PostResponse, PostUpdate

app = FastAPI(title="5주차 · lab 4 완성본에서 시작하기")


def get_db():
    with SessionLocal() as db:
        yield db


@app.get("/health", tags=["연결 확인"])
def health(db: Annotated[Session, Depends(get_db)]):
    db.scalar(select(1))
    return {"status": "ok"}


@app.get("/posts", response_model=list[PostResponse], tags=["게시글"])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Post).order_by(Post.id)).all()


@app.get("/posts/{post_id}", response_model=PostResponse, tags=["게시글"])
def get_post(
    post_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
):
    post = db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


@app.post(
    "/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED, tags=["게시글"]
)
def create_post(body: PostCreate, db: Annotated[Session, Depends(get_db)]):
    author = db.scalars(select(User).where(User.id == body.user_id)).one_or_none()
    if author is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    post = Post(title=body.title, author=author)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.patch("/posts/{post_id}", response_model=PostResponse, tags=["게시글"])
def update_post(
    post_id: Annotated[int, Path(gt=0)],
    body: PostUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    post = db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.title = body.title
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["게시글"])
def delete_post(
    post_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
):
    post = db.scalars(select(Post).where(Post.id == post_id)).one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
