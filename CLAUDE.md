## Project: Helpdesk + Knowledge Base (evolving from fastapi_blog)

> **Current state:** the package is still `src/fastapi_blog/` with a layer-based layout. Paths and
> commands below describe the target after Week 1 of `docs/ROADMAP.md` (rename to `src/helpdesk/`,
> feature layout). Until then, map them to the existing files. See `docs/AUDIT.md` for the gap.

### How Claude should work here — mentor mode
- I am an experienced Java/Spring developer learning Python, FastAPI and AI engineering.
  Act as a mentor and reviewer, not a code generator.
- Default: explain, review my code, and give a **hint first**. Then a fuller explanation if I
  ask. Then a full solution only if I explicitly ask ("write it", "implement it").
- Do not edit source files or run state-changing commands unless I explicitly ask.
  Reading files, running tests, linters and type checkers is always fine.
- When reviewing, point out "Java written in Python" habits and show the Pythonic alternative,
  with a brief "in Spring you'd… / in Python you…" comparison.
- Check which week I'm on in `docs/ROADMAP.md` (the checkboxes) and tie advice back to that
  week's tasks and acceptance criteria. Don't pull in work from future weeks unprompted.
- If a request breaks a convention below, say so and propose the conforming way.

### Conventions
- Layout: by feature (`users/`, `tickets/`, `knowledge/`), each with router, service, models,
  schemas and events. Shared code goes in `core/`. Ports go in `ports/` (typing.Protocol),
  implementations in `adapters/` (fakes in `adapters/fakes/`), AI features in `ai/`.
- `config.py` is the ONLY place environment variables are read (pydantic-settings).
- Core code (`core/`, `users/`, `tickets/`, `knowledge/`) never imports an AI or cloud SDK.
  Only `adapters/` may (LangGraph is also allowed in `ai/agents/`). Ruff `banned-api` enforces this.
- AI features plug in as event subscribers or new adapters. If a feature needs edits to
  `tickets/service.py`, the seam is wrong.
- Services are plain functions taking an `AsyncSession`. No repository layer unless it earns its place.
- Services raise `DomainError` subclasses, never `HTTPException`. Handlers return RFC 9457 problem+json.
- Async everywhere. No blocking calls in `async def`; wrap them with `anyio.to_thread.run_sync`.
- Every LLM-facing feature: testable offline with fakes or respx, and measured by an eval in `evals/`.
- Tooling: `uv` only; `ruff check`, `ruff format`, `mypy --strict` and `pytest` must pass before commit.
- Significant decisions get an ADR in `docs/adr/` (copy `0000-template.md`).

### Commands
- `docker compose up -d` (Postgres 5433, Redis, SeaweedFS) · `uv run alembic upgrade head`
- `uv run fastapi dev src/helpdesk/main.py` · `uv run taskiq worker helpdesk.worker:broker`
- `uv run pytest` · `uv run ruff check . && uv run mypy src`
