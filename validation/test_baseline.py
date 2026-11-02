import pytest


def test_crud(client):
    created = client.post("/posts", json={"title": " 새 글 ", "user_id": 1})
    assert created.status_code == 201
    post = created.json()
    assert post == {"id": post["id"], "title": "새 글", "user_id": 1}
    path = f"/posts/{post['id']}"
    assert client.get(path).json() == post
    updated = client.patch(path, json={"title": "수정"})
    assert updated.status_code == 200
    assert client.get(path).json()["title"] == "수정"
    assert len(client.get("/posts").json()) == 2
    deleted = client.delete(path)
    assert deleted.status_code == 204 and deleted.content == b""
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {"title": "수정"}} if method == "patch" else {}
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 404
        assert response.json() == {"detail": "게시글을 찾을 수 없습니다."}


@pytest.mark.parametrize("title", ["", "   ", "가" * 201])
def test_invalid_titles(client, title):
    assert client.post("/posts", json={"title": title, "user_id": 1}).status_code == 422
    assert client.patch("/posts/1", json={"title": title}).status_code == 422


def test_missing_author(client):
    response = client.post("/posts", json={"title": "글", "user_id": 999})
    assert response.status_code == 404
    assert response.json() == {"detail": "사용자를 찾을 수 없습니다."}


@pytest.mark.parametrize("post_id", ["abc", "0", "-1"])
def test_invalid_ids(client, post_id):
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {"title": "글"}} if method == "patch" else {}
        assert getattr(client, method)(f"/posts/{post_id}", **kwargs).status_code == 422


def test_fresh_data(client):
    assert client.get("/posts").json() == [
        {"id": 1, "title": "첫 번째 글", "user_id": 1}
    ]


def test_openapi(client):
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]["/posts"]) == {"get", "post"}
    assert set(schema["paths"]["/posts/{post_id}"]) == {"get", "patch", "delete"}
