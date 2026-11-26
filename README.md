# Compromised

Know what's been compromised. A plain-language feed of publicly reported security incidents.

Decisions and findings are recorded in [docs/wiki](docs/wiki/index.md).

## Layout

- `api/`: Python (uv). One codebase, two processes: the read-only HTTP API (FastAPI) and the
  ingestion worker. SQL migrations live in `api/src/compromised/storage/migrations/`.
- `web/`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui (pnpm).

## Local development

Needs Homebrew PostgreSQL 17, uv, Python 3.12, Node 25 and pnpm.

One-time setup:

```sh
brew services start postgresql@17
createdb compromised
createdb compromised_test
pnpm install
uv sync --directory api
cp .env.example .env        # optional: every value has a working local default
```

Start the API (http://127.0.0.1:8000), the worker and the web app (http://localhost:3000):

```sh
pnpm dev
```

`pnpm dev` applies pending migrations first. After a migration that adds event classification, or
after changing the classifier rules or the alias dictionary
(`api/src/compromised/data/catalog.json`), run `pnpm db:reclassify` to re-derive every stored
event's category, affected organization and feed tabs. Run it once after migration 010 too: it
fills each stored event's threat actors, attack vector and full search document.

The worker fetches each source when it is due, on its own interval from
`api/src/compromised/sources.py` (The Record: every 5 minutes; Google Threat Intelligence:
hourly). `pnpm worker:once` runs a single pass. Source health and overall ingestion status are at
`/v1/status`. Search and filters are at `/v1/search` (accepted filter values: `/v1/filters`),
Trending at `/v1/trending`.

## Tests

```sh
pnpm test:api     # pipeline, fetcher and API seams (api/tests/{pipeline,fetcher,api}), on compromised_test
pnpm test:e2e     # browser seam (web/e2e), Playwright; seeds compromised_test itself
```

The tests empty `compromised_test`; never point `TEST_DATABASE_URL` or `E2E_DATABASE_URL` at
real data. The browser suite runs its own API and web app on ports 8100 and 3100; set
`E2E_API_PORT` and `E2E_WEB_PORT` to move them. CI (`.github/workflows/ci.yml`) runs all three suites against Postgres 17.

Real captured feed samples used by the tests are in `api/tests/fixtures/real/` with their capture
dates; hand-written inputs are in `api/tests/fixtures/synthetic/` and labelled as such.
