# FastAPI Lab 5 · 완성된 CRUD에 테스트 붙이기

lab 4를 끝낸 코드에서 시작한다. **CRUD를 다시 구현하는 실습이 아니다.** 기존 동작을 테스트로 남기고, 조회 코드를 역할별로 나눈 뒤, 사용자당 게시글 수 제한을 TDD로 추가한다.

## 수업 구성 · 전체 150분

| 구간 | 시간 | 내용 |
|---|---:|---|
| 이론 | 45분 | 구조·DI 12분, 도입 3분, 환경 5분, 문서 5분, TDD 8분, Pytest 12분 |
| 휴식 | 10분 | |
| 실습 | 85분 | 설정 10분 · 코드 읽기 10분 · 테스트 15분 · 역할 분리 5분 · TDD 35분 · 문서 10분 |
| 마무리 | 10분 | 풀이 비교와 질문 |

설치와 MySQL 준비는 수업 전에 완료한다. 구조 분리는 제공 코드를 적용하고 흐름을 읽는다. 직접 작성할 부분은 테스트와 게시글 수 제한이다.

## 제공되는 시작점

- lab 4의 게시글 CRUD 5개: 목록·상세 조회, 생성, 제목 수정, 삭제.
- `User(id, name, age, nickname)`와 `Post(id, title, user_id)` 모델.
- users/posts 생성 → nickname 추가까지 완료된 Alembic 이력.
- lab 4의 요청 검증, 404, 201, 본문 없는 204 동작.
- 테스트마다 새 임시 DB를 만드는 fixture, 시작 테스트 2개, 학생용 TODO 테스트.

기준은 [lab 4의 스켈레톤 커밋](https://github.com/WaffleStudio24-5/fastapi-lab-4/tree/e42ffb8819ff5bf91ef5dbb85577dae23fb8a678)과 이전 이력 `8d9dcf1`의 `solutions/main.py`다. lab 4에서 직접 생성했던 migration은 이 저장소에 재현 가능한 두 revision으로 제공한다. lab 5의 게시글 수 제한 정답은 시작 코드에 포함하지 않는다.

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

## 0-1. .env와 BaseSettings로 설정 읽기 · 10분

설정 코드는 제공되어 있다. `app/settings.py`를 읽고 직접 `.env`를 만들며 동작을 확인한다. 설치·MySQL 준비는 수업 전에 마치고, 이 단계는 실습 85분에 포함한다.

저장소 루트에서 `.env.example`을 복사한다. 이미 `.env`가 있다면 덮어쓰지 말고 필요한 항목만 수정한다.

```bash
cp -n .env.example .env
unset DATABASE_URL
```

PowerShell에서는 `.env`가 없을 때만 `Copy-Item .env.example .env`로 복사하고, `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue`로 기존 환경 변수를 해제한다.

`.env`의 DATABASE_URL은 로컬 실습 MySQL 주소다. 3307을 사용한다면 주소의 포트도 3307로 수정한다. `.env`는 Git에서 제외하고 예시 파일만 공유한다. 이전에 export한 값이 남아 있으면 `.env`보다 우선하므로 해제한 뒤 확인한다.

```python
# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
```

`app/database.py`는 `settings.database_url`로 Engine을 만들고, `migrations/env.py`도 같은 설정을 읽는다. `.env`는 실행한 폴더에서 찾으므로 모든 명령은 저장소 루트에서 실행한다. import할 때 설정 객체를 만들기 때문에 파일을 바꾼 뒤에는 앱을 재시작한다.

다음 명령은 값을 출력하지 않고 설정을 읽을 수 있는지만 확인한다.

```bash
uv run python -c 'from app.settings import settings; print("설정 읽기 성공")'
```

`database_url`에는 기본값이 없어 `.env`와 환경 변수에 값이 모두 없으면 ValidationError가 난다. 아래 자동 검증은 임시 폴더에서 필수값 누락과 우선순위를 확인하므로 실제 `.env`를 지울 필요가 없다.

```bash
uv run python validation/verify_settings.py
```

환경 변수 → `.env` 순으로 읽는다. 테스트의 conftest.py는 앱 import 전에 SQLite 주소를 환경 변수로 지정하므로 `.env`가 MySQL을 가리켜도 테스트는 임시 DB를 사용한다.

### 마이그레이션과 서버 실행

```bash
uv run alembic upgrade head
uv run alembic check
uv run seed.py
uv run nickname.py
uv run uvicorn app.main:app --reload
```

`seed.py`는 빈 users 테이블에서 한 번만 실행한다. 재실행하면 기존 데이터를 보존하고 오류를 낸다. nickname의 초기값은 `None`이다. 앱과 Alembic은 저장소 루트의 `.env`를 읽는다. 새 터미널에서도 저장소 폴더로 이동한 뒤 실행한다.

- 문서: <http://127.0.0.1:8000/docs>
- DB 연결 확인: <http://127.0.0.1:8000/health>
- 게시글 목록: <http://127.0.0.1:8000/posts>
- 종료: `docker compose down` — 볼륨과 데이터는 유지된다.

**lab 4에서 쓰던 DB에 이 migration을 적용하지 않는다.** 학생마다 lab 4 revision ID가 다르다. 이 저장소 전용 `seminar_lab5` 빈 DB에서 시작한다. Compose의 비밀번호는 로컬 학습용이며 운영에 사용하지 않는다.

## 테스트 실행

```bash
uv run pytest -q
```

초기 예상 결과: **2 passed, 6 skipped**. skip은 학생이 아직 작성하지 않은 테스트다. 테스트 실행에는 MySQL·Uvicorn·DATABASE_URL 설정이 필요하지 않다.

`tests/conftest.py`는 앱을 불러오기 전에 테스트 프로세스의 DB 주소를 메모리 SQLite로 고정한다. 테스트마다 DB를 새로 만들고 사용자 1명과 게시글 1개를 넣는다. `app.dependency_overrides`로 `get_db`를 교체하므로 테스트 요청은 이 DB만 사용한다. 요청마다 세션을 새로 열어 커밋한 변경을 다음 요청에서 확인한다.

SQLite 테스트는 API 응답과 SQLAlchemy 연결을 빠르게 확인한다. MySQL의 자료형·정렬·제약 조건·migration 동작까지 보장하지 않는다. 실제 MySQL 검증은 아래 별도 명령으로 실행한다.

## 1. 실행과 테스트 읽기 · 10분

`app/main.py`의 CRUD와 `tests/test_start.py`를 읽는다. `test_read_post`에서 준비(Arrange)는 fixture, 실행(Act)은 GET 요청, 검증(Assert)은 상태 코드와 본문 비교다.

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

완료 기준: **7 passed, 1 skipped**.

## 3. 역할을 나눈 코드 적용하기 · 5분

[노션 실습 3단계](https://app.notion.com/p/40cdf97f025781a89b42c23697cd569b)의 파일별 코드를 적용하고, 요청이 Router → Service → Repository를 거치는 흐름을 확인한다.

```bash
uv run pytest -q
uv run pytest -q tests/test_start.py validation
```

TODO 1–3을 마쳤다면 첫 명령은 **7 passed, 1 skipped**, 두 번째는 **12 passed**다.

## 4. 사용자당 게시글을 최대 3개로 제한하기 · 35분

같은 사용자가 이미 글을 3개 작성했다면 추가 작성 요청에 **409 Conflict**를 반환한다. 2개에서 3개가 되는 작성은 허용한다. 테이블 구조는 그대로이므로 새 migration은 필요 없다.

1. TODO 4의 skip을 지우고 `from app.models import Post`를 추가한다.
2. `session_factory.begin()` 안에서 사용자 1의 글을 두 개 더 넣는다. 기존 글까지 총 3개다.
3. 블록 밖에서 POST로 네 번째 글을 요청한다. 409와 오류 본문을 확인하고, DB의 해당 사용자 글 수가 여전히 3인지 확인한다.
4. 기대한 409 대신 201이 나와 실패하는지 확인한다. import 오류는 이번에 확인할 Red가 아니다.
5. Service의 `create_post()`에서 작성자의 글 수를 검사한다. 한도에 도달하면 `ValueError`를 발생시키고 저장하지 않는다. Router는 이를 잡아 HTTPException으로 409를 반환한다.
6. 테스트를 통과시킨 뒤 코드를 정리한다. 작성자 확인과 기존 CRUD도 유지한다.

이번 실습의 오류 본문은 다음으로 통일한다.

```json
{"detail": {"message": "사용자는 최대 3개까지 글을 작성할 수 있습니다."}}
```

완료 기준: **8 passed**, skip 없음. 예외는 POST 처리에서만 잡는다. 다른 실패 이유가 늘어난다면 별도 예외 타입을 고려한다.

| 추가 확인 | 기대 결과 |
|---|---|
| 작성자의 글이 2개 | 201, 작성 후 3개 |
| 작성자의 글이 3개 | 409, 거절 후에도 3개 |
| 다른 사용자에게 글이 많이 있음 | 현재 작성자의 한도에 영향을 주지 않음 |
| 존재하지 않는 작성자 | 기존 404 |

실습 결과 코드처럼 목록에서 작성자의 글을 골라 개수를 세어도 된다. 데이터가 많다면 Repository의 사용자별 COUNT 쿼리로 개선할 수 있다. 개수 확인과 저장 사이에 다른 요청이 들어올 수 있으므로, 이 구현은 동시 요청까지 한도를 보장하지 않는다.

## 5. API 문서와 테스트 확인 · 10분

- POST description에 최대 3개까지 작성할 수 있음을 설명한다.
- responses에 409 설명을 추가한다. 문서 설정이 실제 오류 처리를 대신하지는 않는다.
- Service의 한도 검사를 잠깐 제거해 TODO 4가 실패하는지 확인한 뒤 복원한다.
- `uv run pytest -q tests validation`을 실행한다. 제공된 TODO를 모두 완성했다면 **18 passed**가 기준이다.

## 실습을 마쳤다면

- [ ] TODO 1–4를 작성하고 skip을 모두 제거했다.
- [ ] CRUD가 Router → Service → Repository를 거치며 기존 404·422·201·204를 유지한다.
- [ ] 세 번째 글은 허용하고, 네 번째 글은 409로 거절한다.
- [ ] 거절한 요청이 DB에 게시글을 추가하지 않는다.
- [ ] POST의 실제 응답과 문서의 409 설명이 일치한다.

## 진행자용 검증

```bash
uv run pytest -q tests/test_start.py validation
uv run python validation/verify_mysql.py
uv run python validation/verify_settings.py
```

첫 명령은 CRUD·404·422·204·테스트 데이터 독립성과 OpenAPI 경로를 확인한다. 시작 코드는 **12 passed**가 예상 결과다. 학생 TODO를 제외하므로 이 결과만으로 한도 제한을 검증했다고 할 수 없다.

두 번째 명령은 Docker가 필요하다. 별도의 임시 MySQL 컨테이너에서 migration·기존 데이터 보존·seed·CRUD·빈 DB 재적용을 확인하고 컨테이너를 정리한다. 기존 MySQL 데이터는 사용하지 않는다.

현재 잠금 파일은 TestClient용 `httpx2`를 사용한다. `uv sync --locked`로 같은 환경을 설치한다. SQLite 테스트 통과가 MySQL 동작이나 동시 요청의 정확성을 보장하지는 않는다.
