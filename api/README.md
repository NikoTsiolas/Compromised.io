# Compromised API and worker

One Python codebase, two processes: the read-only HTTP API and the ingestion worker. The module
map is in `src/compromised/__init__.py`. Local setup is in the repository README.

```sh
uv run python -m compromised.storage migrate                  # apply SQL migrations
uv run uvicorn compromised.api:create_app --factory --port 8000
uv run python -m compromised.worker [--once]
uv run pytest                                                  # pipeline, fetcher and API seams
```

Tests use the `compromised_test` database (override with `TEST_DATABASE_URL`).
