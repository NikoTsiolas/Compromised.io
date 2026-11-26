# Stack and hosting

- 2026-11-26: Stack from the brief, kept: Next.js, TypeScript and Tailwind for the frontend; Python and FastAPI for the API; PostgreSQL; asyncio, httpx and feedparser for ingestion; a simple scheduled worker; PostgreSQL full-text search. No Redis, vector store or microservices.
- 2026-11-26: One repository with `api/` and `web/`; uv for Python, pnpm for Node. Remote: `NikoTsiolas/Compromised.io` (private, empty on this date).
- 2026-11-26: Hosting: Vercel for the frontend; Railway for the API, the ingestion worker (a second process from the same Python codebase) and Postgres. Niko had not used Vercel before and chose it.
- 2026-11-26: Niko asked whether Vercel or Supabase would handle the database. Answer given: Vercel hosts only the site; the database belongs beside the worker on Railway; Supabase adds auth the project does not need.
- 2026-11-26: Local development uses Postgres 17 from Homebrew, pinned to the version Railway provisions. The machine had Node 25, npm, Python 3.12, uv and gh; no Docker, Postgres or pnpm. A compose file is included for those who prefer Docker.
- 2026-11-26: Niko buys the domain himself through Cloudflare. A whois lookup returned "Domain not found" for `compromised.io`.
- 2026-11-26: A subagent could not verify which Postgres major version Railway provisions by default; indirect evidence suggested 18. Local development started on Homebrew Postgres 17 as agreed; the pin is to be revisited when the Railway database is created. Nothing in the spec depends on a 17-versus-18 difference.

## Walking skeleton, 2026-11-26
As of `NikoTsiolas/Compromised.io@93f06cc` (ticket #2, built by an Opus subagent, CI green on that commit):
- `pnpm dev` from the repo root applied migrations and started the API on :8000, the worker and the web app on :3000.
- Migrations were numbered `.sql` files run by a small built-in runner tracked in a `schema_migrations` table; Alembic was not used.
- Events sorted by `published_at` descending then `id`; the cursor was opaque base64 of those two values.
- The deduplicator was a stand-in: it skipped a record whose canonical URL, or source plus guid, was already stored, and gave every other record its own event. Ticket #5 replaces it.
- The fetcher allowed HTTPS only, followed no redirects, and took its user agent from `USER_AGENT`, which pointed at the GitHub repo pending the domain.
- Next.js 16 had `cacheComponents` on by default, so pages that fetch data had to sit inside `<Suspense>`.
- shadcn used `@base-ui/react` and its own `cn` package in place of clsx and tailwind-merge.
- The browser suite seeded `compromised_test` with the real BleepingComputer capture plus one item labelled synthetic; the seed script refused to run with `ENVIRONMENT=production`.
- A real run on this date stored 15 events from BleepingComputer and created none on the second fetch.

Friction the subagent reported: its worktree started one commit behind `mvp`; the worktree guard rejected heredocs and `git -C`; macOS has no `timeout` command.
