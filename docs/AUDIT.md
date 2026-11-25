# Audit — `fastapi_blog` against the helpdesk "socket" target

_Date: 2026-11-23 · Scope: everything under `fastapi_blog/` except `.venv/` and `.idea/` · Read-only review_

## 0. Snapshot

| Item | Finding |
|---|---|
| Size | ~200 lines of Python, 1 entity (`User`), 2 endpoints (`POST /users/`, `GET /users/{id}`), 1 Alembic migration |
| Entry points | `src/fastapi_blog/main.py` (`app`). `[project.scripts] fastapi-blog` → `fastapi_blog:main`, which only prints "Hello from fastapi-blog!" (leftover `uv init` boilerplate) |
| Layout | `src/` layout, organised by technical layer: `api/`, `services/`, `repositories/`, `models/`, `schemas/`, `db/`, `core/`, plus `templates/` and `static/` |
| Persistence | Sync SQLAlchemy 2.x (`Mapped`/`mapped_column`), psycopg 3, one session per request through `get_db` |
| Tests | `tests/` exists but is empty |
| Tooling | uv + `uv.lock`. No ruff, type checker, pre-commit, Dockerfile, Compose or CI |
| Docs | `README.md` is empty; the `pyproject.toml` description is still the placeholder |
| Git | Repo initialised on branch `dev/part1` with **zero commits**. The index is inconsistent: every file is staged under a stale `fastapi_blog/…` prefix (status `AD`), while the real files at the root are untracked (`??`) |

### Versions (lockfile vs. PyPI, checked 2026-11-23)

| Package | Locked | Latest | Note |
|---|---|---|---|
| Python | 3.14.4 | 3.14.x | Current |
| fastapi | 0.162.2 | 0.165.0 | Minor drift, run `uv lock --upgrade` |
| starlette | 1.10.0 | 1.10.0 | ✅ |
| pydantic | 2.14.3 | 2.14.4 | Patch |
| pydantic-settings | 2.16.2 | 2.16.3 | Patch. Imported directly but **not declared** (only present through `fastapi[standard]`) |
| sqlalchemy | 2.1.8 | 2.1.9 | Patch |
| alembic | 1.20.1 | 1.20.1 | ✅ |
| psycopg | 3.3.9 | 3.3.9 | ✅ |
| uvicorn | 0.54.0 | 0.54.0 | ✅ |
| python-dotenv | 1.2.4 | 1.2.4 | Imported directly but not declared, and not needed once config is unified |
| email-validator | 2.3.0 | 2.4.0 | Installed but unused (`EmailStr` isn't used) |

**Deprecated patterns:** none. There's no Pydantic v1 API (`ConfigDict` is used, not `class Config`), no SQLAlchemy 1.x `Query` API, and no `@app.on_event` (`lifespan` is used). That's a good sign.

---

## A. 12-Factor App

| # | Factor | Status | Justification |
|---|---|---|---|
| 1 | Codebase | ⚠️ | A repo exists (`.git`, branch `dev/part1`, remote `origin`), but it has no commits, and the index tracks a stale `fastapi_blog/` path prefix while the real files are untracked. There is no deployable revision yet. |
| 2 | Dependencies | ⚠️ | `pyproject.toml` + `uv.lock` ✅. But `pydantic-settings` (`core/config.py:1`) and `python-dotenv` (`db/database.py:3`, `alembic/env.py:5`) are imported without being declared. There's no `[dependency-groups] dev`. |
| 3 | Config | ⚠️ | `core/config.py` uses pydantic-settings ✅ and there are no secrets in code ✅. But env vars are read in **three** places (`core/config.py`, `db/database.py:9-12` with a dead `DATABASE_URL` variable, `alembic/env.py:15-20`). `env_file=".env"` is relative to the current directory: importing `fastapi_blog.main` from `src/` fails with `DATABASE_URL Field required` (reproduced). `echo=True` is hard-coded (`db/database.py:15`). `alembic.ini:89` falls back to a placeholder URL. There's no `.env.example`. |
| 4 | Backing services | ⚠️ | Postgres is attached through a URL ✅. There's no Redis, object storage, LLM or vector store, and no abstraction to swap them. |
| 5 | Build, release, run | ❌ | No Dockerfile, no image, no CI pipeline. |
| 6 | Stateless processes | ✅ | No in-process state. A new session per request (`db/database.py:23-28`). This is trivially true so far. |
| 7 | Port binding | ⚠️ | Works through `fastapi dev`/uvicorn (from `fastapi[standard]`), but no run command is documented, `PORT` isn't configurable, and the console script is a placeholder (`__init__.py`). |
| 8 | Concurrency | ❌ | A single `api` process. No worker process, no queue. |
| 9 | Disposability | ⚠️ | `lifespan` exists but is empty (`main.py:8-10`). The engine is never disposed, and there's no graceful-shutdown handling. |
| 10 | Dev/prod parity | ❌ | No Compose file. Postgres runs as a hand-started container. There's no local stand-in for S3 or LLM providers. |
| 11 | Logs | ❌ | `print()` in `api/user_controller.py:23` and `repositories/user_repository.py:18`, plus SQLAlchemy `echo`. No structured logging. |
| 12 | Admin processes | ⚠️ | Alembic is configured, with one migration ✅. `alembic/env.py` has duplicated config (`config = context.config` on lines 17 and 29), a `sys.path` hack (lines 10-12) and a single-model import (line 23) that will silently miss new models during autogenerate. There's no CLI for seed/ingest/reindex. |

## B. FastAPI / Python engineering practices

| Practice | Status | Justification |
|---|---|---|
| Project layout | ⚠️ | `src/` layout ✅, but organised by technical layer (Spring style). Every feature will touch 5–6 folders. |
| `Depends`-based DI | ✅ | Clean `get_db → get_user_repository → get_user_service` chain with `Annotated` (`api/dependencies.py`). |
| Async correctness | ✅ | Sync `def` endpoints + sync `Session` is correct, because FastAPI runs them in a threadpool. There are no blocking calls inside `async def`. (Moving to async is a design choice for the helpdesk, not a bug fix.) |
| Pydantic v2 schemas separate from ORM | ⚠️ | Separated ✅. But `UserCreate` has no validation (`email: str`, no length limits matching the `String(50)`/`String(120)` columns), and `from_attributes=True` is unnecessary on an input schema (`schemas/user_create.py:8`). |
| Error handling | ❌ | The service raises `HTTPException` (`services/user_service.py:23`), which mixes HTTP into the domain layer. A duplicate username or email raises `IntegrityError` → **500**, with no rollback. There are no exception handlers. |
| API versioning | ❌ | Routes are mounted at `/users`, with no `/api/v1` prefix. |
| Auth | ❌ | None. Passwords are **stored in plain text** (`services/user_service.py:12`). |
| Pagination | ❌ | There are no list endpoints yet. |
| Testing | ❌ | `tests/` is empty. No pytest, httpx, fixtures or testcontainers. |
| Typing | ⚠️ | Mostly annotated. `UserRepository.create_user` is annotated `-> UserResponse \| None` but returns a `User` (`repositories/user_repository.py:11`). `get_user_by_id` in the service has no return type. No type checker runs. |
| Lint/format, pre-commit | ❌ | No ruff, no pre-commit. |
| Observability | ❌ | No health/readiness endpoints, no request IDs, no OpenTelemetry. |
| Security basics | ❌ | Plain-text passwords. No auth, CORS policy or rate limiting. |
| Dead/unwired code | ⚠️ | `templates/` and `static/` aren't mounted in `main.py`, and `layout.html` calls `url_for('home')`/`url_for('posts')`, which don't exist, so rendering would crash. The empty `lifespan` and placeholder `main()` are also unused. |

### Spring habits worth unlearning

| Spring habit in this repo | Where | Pythonic equivalent |
|---|---|---|
| `*Controller` naming | `api/user_controller.py` | `users/router.py`, where `router = APIRouter(...)` |
| One class per file for DTOs | `schemas/user_create.py`, `schemas/user_response.py` | One `schemas.py` per feature. Python modules group related things. |
| `_model` suffix inside a `models` package | `models/user_model.py` | `users/models.py`. The package already says what it is. |
| Throwing an HTTP status from the service (`ResponseStatusException`) | `services/user_service.py:23` | A plain domain exception (`class UserNotFound(Exception)`), mapped to a 404 by a handler registered once in `main.py` |
| A repository class that just passes calls through to the ORM (Spring Data reflex) | `repositories/user_repository.py` | SQLAlchemy's `Session` already *is* a unit of work. Add a repository only where it earns its place: query composition, or as a **Protocol port** you can fake. Otherwise use plain functions that take a `Session`. |
| Constant-style config fields | `core/config.py:5` (`DATABASE_URL`) | Use `database_url: PostgresDsn`. pydantic-settings matches env vars case-insensitively, and Python attributes are snake_case. |
| Logging with `System.out.println` | `print()` in the controller and repository | `logger = logging.getLogger(__name__)`, configured once in `core/logging.py` |

What's **not** a Spring habit and should stay: the `Depends` provider functions. They play the role of `@Bean` factories, but they're idiomatic FastAPI, and they're how `app.dependency_overrides` makes testing easy.

## C. Socket readiness

| Seam | Status | Justification |
|---|---|---|
| Domain events | ❌ | No event types, no publisher, no queue, no subscribers. |
| Ports as `typing.Protocol` | ❌ | No `ports/` package. `UserRepository` is a concrete class injected directly. There are no LLM/embedding/vector/storage interfaces or fakes. |
| Settings-driven adapter selection | ❌ | `Settings` has no provider fields. |
| No AI SDK in core | ✅ | Trivially true, since there are no AI SDKs. |

The DI chain in `api/dependencies.py` is the exact place where Protocol-typed ports will be wired, so that pattern carries over directly.

## D. Fit with the helpdesk target

| Piece | Verdict | Notes |
|---|---|---|
| `User` model + `UserCreate`/`UserResponse` | **Reuse and extend** | Add `role`, `team_id`, `is_active`, `created_at`. Fix validation and hashing. |
| `core/config.py` | **Reuse and fix** | Becomes the *only* place env vars are read. Lowercase fields, absolute `env_file`, provider settings. |
| `db/database.py` + `get_db` | **Reuse and fix** | Remove the dotenv code, make `echo` configurable, dispose the engine in `lifespan`. Decide sync vs async (ADR). |
| `api/dependencies.py` DI chain | **Reuse the pattern** | Same shape, different types. |
| Alembic setup | **Reuse and fix** | Import settings and `fastapi_blog.models`, drop the `sys.path` hack. The single migration is disposable. |
| Layer-based folders | **Migrate** | Move to a feature layout (`users/`, `tickets/`, `knowledge/`, `core/`). |
| `templates/`, `static/` | **Drop** | Blog-specific, unwired, and the helpdesk is API-first. |
| Package name `fastapi_blog` | **Rename** | A portfolio project should be named after its domain. |
| Git state | **Restart** | No commits to preserve, and the index is inconsistent. |

**Honest assessment:** starting fresh is cheaper. There's nothing meaningful to preserve in history (zero commits). The domain doesn't match (blog ≠ helpdesk). The layout, package name and migration would all change anyway. What *is* worth keeping is about five files' worth of patterns (config, session, DI chain, Alembic `env.py`, the `User` model). Porting them by hand into a new `helpdesk` repo is a good Week-1 exercise in itself, because every line you carry over gets fixed on the way. Keep `fastapi_blog` as a finished course exercise rather than trying to bend it into the portfolio project.

> **Decision (2026-11-23): evolve `fastapi_blog` in place.** The roadmap's Week 1 therefore starts with repairing the git index, renaming the package to `helpdesk`, and restructuring by feature. The same fixes apply; they're just done as moves within this repo instead of a port to a new one.

---

## Top 5 issues to fix first

1. **Get to a clean first commit (factor 1).** Today there's no history, and the index points at paths that no longer exist. Nothing else (CI, code review, ADRs, "show me your progress") works without version control. Whether in this repo or a fresh `helpdesk` repo, the first task is `git init` → correct `.gitignore` → first commit.
2. **Plain-text passwords** (`services/user_service.py:12`). It's a security bug and the first thing an interviewer will spot. Hash with `pwdlib[argon2]` behind a small `core/security.py`. Auth (Week 1) depends on it anyway.
3. **Config read in three places, with a CWD-relative `.env`** (`core/config.py`, `db/database.py`, `alembic/env.py`). This is the foundation of factors 3, 4 and 10. Every adapter you add in Phases 2–4 (LLM provider, vector store, storage) is selected through `Settings`, so it has to be the single source of truth before you add any of them.
4. **No error model** (`HTTPException` in the service, `IntegrityError` → 500, no input validation). This sets the pattern for every feature after it. Domain exceptions plus handlers registered once means services can be called from routers, workers, CLI commands and agent tools alike. That is exactly what the socket design requires.
5. **No tooling or tests** (no ruff, type checker, pytest or pre-commit). Adding these on day one costs an hour; adding them to 3,000 lines costs a weekend of fixes. Phases 2–4 depend on "testable without network calls", which needs a pytest + fakes setup from the start.

Not in the top 5, but decided by the fresh-start choice: **the feature-based layout**. Do it before the second entity exists.
