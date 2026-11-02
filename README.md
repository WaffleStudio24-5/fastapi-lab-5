# FastAPI Lab 5 · 완성된 CRUD에 테스트 붙이기

lab 4를 끝낸 코드에서 시작한다. **CRUD를 다시 구현하는 실습이 아니다.** 기존 동작을 테스트로 남기고, 조회 코드를 역할별로 나눈 뒤, 공개 여부 규칙을 TDD로 추가한다.

## 수업 구성 · 전체 150분

| 구간 | 시간 | 내용 |
|---|---:|---|
| 이론 | 45분 | 구조·DI 12분, 도입 3분, 환경 5분, 문서 5분, TDD 8분, Pytest 12분 |
| 휴식 | 10분 | |
| 실습 | 85분 | 아래 1–5단계 |
| 마무리 | 10분 | 풀이 비교와 질문 |

설치와 MySQL 준비는 수업 전에 완료한다. 85분 안에는 **목록·상세 조회만 구조를 분리**한다. 생성·수정·삭제의 구조 분리는 선택 과제다.

## 제공되는 시작점

- lab 4의 게시글 CRUD 5개: 목록·상세 조회, 생성, 제목 수정, 삭제.
- `User(id, name, age, nickname)`와 `Post(id, title, user_id)` 모델.
- users/posts 생성 → nickname 추가까지 완료된 Alembic 이력.
- lab 4의 요청 검증, 404, 201, 본문 없는 204 동작.
- 테스트마다 새 임시 DB를 만드는 fixture, 시작 테스트 2개, 학생용 TODO 테스트.

기준은 [lab 4의 스켈레톤 커밋](https://github.com/WaffleStudio24-5/fastapi-lab-4/tree/e42ffb8819ff5bf91ef5dbb85577dae23fb8a678)과 이전 이력 `8d9dcf1`의 `solutions/main.py`다. lab 4에서 직접 생성했던 migration은 이 저장소에 재현 가능한 두 revision으로 제공한다. lab 5의 리팩토링·비공개 기능 정답은 시작 코드에 포함하지 않는다.

## 수업 전 준비

Python 3.12 이상, uv, Git, Docker가 필요하다. 터미널은 저장소 루트에서 연다.

```bash
git clone https://github.com/WaffleStudio24-5/fastapi-lab-5.git
cd fastapi-lab-5
uv sync --locked
docker compose up -d --wait
```

기본 포트는 3306이다. lab 4 MySQL이 이미 3306을 쓰고 있다면 기존 컨테이너를 지우지 않고 lab 5를 3307로 실행한다.

macOS/Linux:

```bash
MYSQL_PORT=3307 docker compose up -d --wait
```

Windows PowerShell:

```powershell
$env:MYSQL_PORT = "3307"
docker compose up -d --wait
```

앱에 접속 주소를 전달한다. 3307을 사용했다면 아래 주소도 3307로 바꾼다.

macOS/Linux:

```bash
export DATABASE_URL='mysql+pymysql://seminar:lab5-local-only@127.0.0.1:3306/seminar_lab5?charset=utf8mb4'
```

Windows PowerShell:

```powershell
$env:DATABASE_URL = "mysql+pymysql://seminar:lab5-local-only@127.0.0.1:3306/seminar_lab5?charset=utf8mb4"
```

```bash
uv run alembic upgrade head
uv run alembic check
uv run seed.py
uv run nickname.py
uv run uvicorn main:app --reload
```

`seed.py`는 빈 users 테이블에서 한 번만 실행한다. 재실행하면 기존 데이터를 보존하고 오류를 낸다. nickname의 초기값은 `None`이다. 앱은 `.env`를 자동으로 읽지 않으므로 새 터미널에서는 `DATABASE_URL`을 다시 설정한다.

- 문서: <http://127.0.0.1:8000/docs>
- DB 연결 확인: <http://127.0.0.1:8000/health>
- 게시글 목록: <http://127.0.0.1:8000/posts>
- 종료: `docker compose down` — 볼륨과 데이터는 유지된다.

**lab 4에서 쓰던 DB에 이 migration을 적용하지 않는다.** 학생마다 lab 4 revision ID가 다르다. 이 저장소 전용 `seminar_lab5` 빈 DB에서 시작한다. Compose의 비밀번호는 로컬 학습용이며 운영에 사용하지 않는다.

## 테스트 실행

```bash
uv run pytest -q
```

초기 예상 결과: **2 passed, 7 skipped**. skip은 학생이 아직 작성하지 않은 테스트다. 테스트 실행에는 MySQL·Uvicorn·DATABASE_URL 설정이 필요하지 않다.

`tests/conftest.py`는 앱을 불러오기 전에 테스트 프로세스의 DB 주소를 메모리 SQLite로 고정한다. 테스트마다 DB를 새로 만들고 사용자 1명과 게시글 1개를 넣는다. `app.dependency_overrides`로 `get_db`를 교체하므로 테스트 요청은 이 DB만 사용한다. 요청마다 세션을 새로 열어 커밋한 변경을 다음 요청에서 확인한다.

SQLite 테스트는 API 응답과 SQLAlchemy 연결을 빠르게 확인한다. MySQL의 자료형·정렬·제약 조건·migration 동작까지 보장하지 않는다. 실제 MySQL 검증은 아래 별도 명령으로 실행한다.

## 1. 실행과 테스트 읽기 · 10분

`main.py`의 CRUD와 `tests/test_start.py`를 읽는다. `test_read_post`에서 준비(Arrange)는 fixture, 실행(Act)은 GET 요청, 검증(Assert)은 상태 코드와 본문 비교다.

`tests/conftest.py`의 `yield` 앞에서 무엇을 준비하고 뒤에서 무엇을 정리하는지 확인한다. `session_factory`는 새 세션을 만드는 함수다. 테스트 데이터는 앱의 MySQL 데이터와 별개다.

## 2. 기존 동작을 테스트로 남기기 · 15분

`tests/test_exercises.py`의 TODO 1–3에서 `pytest.skip(...)`을 지우고 테스트를 작성한다.

| 요청 | 기대 결과 |
|---|---|
| `GET /posts/999` | 404, `{"detail": "게시글을 찾을 수 없습니다."}` |
| `GET /posts/abc`, `/posts/0`, `/posts/-1` | 422 |
| `POST /posts`에 `{"title": "새 글", "user_id": 1}` | 201, 생성된 ID·제목·작성자 |
| 생성된 ID로 GET | POST에서 받은 본문과 동일 |

생성된 ID를 응답에서 읽는다. 422 오류 본문 전체는 라이브러리 버전에 따라 달라질 수 있으므로 필요하면 오류 위치를 확인한다. 이 단계는 이미 있는 동작에 테스트를 붙이는 것이며 TDD는 아니다.

완료 기준: **7 passed, 2 skipped**.

## 3. 조회 코드의 역할 나누기 · 20분

다음 파일은 직접 만든다. 클래스 이름을 외우기보다 SQL·규칙·HTTP를 어디서 처리하는지 확인한다.

```text
main.py          앱 생성, 기존 쓰기 API, 조회 router 등록
dependencies.py  기존 get_db를 이동 (SessionLocal은 database.py에 유지)
repositories.py  PostRepository(db): get(post_id), list()
services.py      PostService(repository): get_post(post_id), list_posts()
routers.py       APIRouter, GET /posts, GET /posts/{post_id}, get_service
```

- Repository로 기존 `select()` 조회를 이동한다. 단건은 Post 또는 None, 목록은 ID 오름차순 Post 목록을 반환한다.
- Service는 우선 Repository 결과를 그대로 전달한다. 다음 단계에서 공개 여부 규칙을 맡는다.
- Router는 기존 Path 검증, response_model, 404 본문을 유지한다.
- `get_service(db=Depends(get_db))`에서 `PostService(PostRepository(db))`를 준비한다.
- `main.py`에서 기존 GET 두 개를 제거하고 `app.include_router(...)`로 연결한다. 경로를 중복 등록하지 않는다.
- `get_db`는 `dependencies.py`의 동일한 함수 객체를 모든 라우트에서 사용한다. fixture도 `from dependencies import get_db`로 고친다. `from main import app`은 유지한다.
- 쓰기 API와 health에도 이동한 `get_db`를 import한다. `routers.py`에서 main을 import하면 순환 import가 생기므로 피한다.

각 이동 후 테스트를 실행한다. **7 passed, 2 skipped**를 유지하면 다음 단계로 간다. 이때 Service의 단순 전달은 다음 규칙을 넣기 위한 중간 상태다.

## 4. 비공개 게시글 숨기기 · 25분

이번 요구사항: **공개 조회에서 비공개 글은 상세 조회 404, 목록에서는 제외한다.** 인증 기능은 만들지 않는다. 기존 생성 API는 계속 공개 글을 만든다. 비공개 데이터는 테스트 fixture 또는 DB 세션으로 준비한다.

### 준비 · 스키마 변경

`models.py`에서 `Boolean`, `true`를 import하고 Post에 다음 열을 추가한다. 기존 글도 공개 상태가 되도록 서버 기본값을 둔다.

```python
is_public = Column(Boolean, nullable=False, default=True, server_default=true())
```

```bash
uv run alembic revision --autogenerate -m "add post is_public"
uv run alembic upgrade head
uv run alembic check
```

생성 파일이 posts에 Boolean 열을 추가하는지 확인한다. 요청·응답 스키마는 변경하지 않는다. SQLite 테스트 DB는 fixture가 모델에서 새로 만들기 때문에 migration을 실행하지 않는다.

### Red → Green → Refactor

1. TODO 4에서 제공된 `session_factory.begin()` 컨텍스트로 ID 1의 `Post.is_public`을 False로 바꾼다. `GET /posts/1`의 404와 오류 본문을 검증한다.
2. 테스트가 **기대한 404 대신 200이라서 실패**하는지 확인한다. import 오류·열 누락은 Red가 아니다.
3. Service의 단건 조회에 공개 여부 규칙을 추가해 통과시킨다. Repository는 비공개 글도 그대로 조회한다.
4. TODO 5에서 비공개 글을 추가하고, 목록에는 기존 공개 글만 남는지 검증한다. 실패를 본 다음 Service의 목록 처리에 규칙을 넣는다.
5. 전체 테스트를 실행한다. 없는 글의 404와 공개 글의 200도 유지해야 한다.

완료 기준: **9 passed**, skip 없음. 쓰기 API에는 인증·소유권 확인이 없으므로 이 실습을 실제 서비스의 비공개 기능으로 배포해서는 안 된다.

## 5. 문서와 테스트 확인 · 10분 + 여유 5분

- 조회 API의 summary와 description에 공개 글만 조회한다는 규칙을 쓴다.
- 상세 조회의 responses에 404를 설명한다. 문서 설정이 오류 처리를 구현해 주지는 않는다.
- 단건 공개 여부 검사를 잠깐 제거한다. 비공개 글 테스트가 실패하는지 본 뒤 복원한다.
- 목록 필터도 같은 방법으로 확인한다. 마지막에 전체 테스트가 통과해야 한다.

## 시작 코드 검증 · 진행자용

```bash
uv run pytest -q tests/test_start.py validation
uv run python validation/verify_mysql.py
```

첫 명령은 시작 CRUD의 생성·조회·수정·삭제, 404·422, 테스트 데이터 독립성, OpenAPI 경로를 확인한다. 학생 TODO 파일은 기본 검증에서 제외된다. 두 번째 명령은 Docker가 필요하며 독립적인 임시 MySQL 컨테이너에서 migration·seed·CRUD를 확인하고 컨테이너를 정리한다. 기존 MySQL 주소와 데이터는 사용하지 않는다.

잠금 파일은 lab 4의 의존성 버전을 이어받는다. 현재 Starlette에서 HTTPX TestClient 사용에 대한 폐기 예정 경고가 한 번 표시되지만 테스트 실패는 아니다. 수업 중 임의 업그레이드하지 말고 `uv sync --locked`로 같은 버전을 사용한다.

시간이 남으면 쓰기 API의 구조 분리, Service에 가짜 Repository를 주입한 단위 테스트, 별도 테스트 MySQL을 사용하는 pytest fixture를 추가한다. 수업 필수 범위에는 포함하지 않는다.
