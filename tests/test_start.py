def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_read_post(client):
    response = client.get("/posts/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "첫 번째 글", "user_id": 1}
