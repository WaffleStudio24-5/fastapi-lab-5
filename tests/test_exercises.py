"""skip 줄을 지우고 직접 작성한다."""
import pytest


def test_missing_post(client):
    pytest.skip("TODO 1: GET /posts/999의 상태 코드와 본문 확인")


@pytest.mark.parametrize("post_id", ["abc", "0", "-1"])
def test_invalid_post_id(client, post_id):
    pytest.skip("TODO 2: 잘못된 ID는 422")


def test_create_then_read(client):
    pytest.skip("TODO 3: POST의 201과 다음 GET의 본문 확인")


def test_three_posts_per_user(client, session_factory):
    pytest.skip("TODO 4: 글이 3개인 사용자의 추가 작성은 409이며 저장된 글도 3개인지 확인")
