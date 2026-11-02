"""skip 줄을 지우고 직접 작성한다. 건너뛴 테스트는 검증 완료가 아니다."""
import pytest


def test_missing_post(client):
    pytest.skip("TODO 1: GET /posts/999의 상태 코드와 본문 확인")


@pytest.mark.parametrize("post_id", ["abc", "0", "-1"])
def test_invalid_post_id(client, post_id):
    pytest.skip("TODO 2: 잘못된 ID는 422")


def test_create_then_read(client):
    pytest.skip("TODO 3: POST의 201과 다음 GET의 본문 확인")


def test_private_post_is_hidden(client, session_factory):
    pytest.skip("TODO 4: is_public을 추가한 뒤 비공개 글의 GET은 404")


def test_list_excludes_private_posts(client, session_factory):
    pytest.skip("TODO 5: 목록에도 비공개 글이 나오지 않는지 확인")
