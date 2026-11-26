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

## Grouping as built, 2026-11-26
As of `NikoTsiolas/Compromised.io@37d315a` (ticket #5, built by an Opus subagent); supersedes the stand-in deduplicator described under "Walking skeleton":
- Order of evidence, first hit wins: identical canonical URL from another source; a shared CVE identifier within 7 days; same affected organization (catalog key, else name) plus pg_trgm `similarity()` of headlines at least 0.2 within 72 hours. Otherwise a new event. All three numbers are configuration: `GROUPING_HEADLINE_SIMILARITY`, `GROUPING_CVE_WINDOW_DAYS`, `GROUPING_ORGANIZATION_WINDOW_HOURS`.
- Two guards beyond the spec, both from the real samples: a record naming CVEs never joins, by headline, an event whose records name only other CVEs (MSRC's two Windows flaws scored 0.26 and 0.29); and headline similarity only links records from different sources (no real feed carried two items about one incident).
- Evidence for the threshold, real samples captured 2026-11-26: the 1Password breach headlines from BleepingComputer, Security Affairs and The Hacker News scored 0.217, 0.299 and 0.591 pairwise; .NET (Dark Reading vs MSRC) 0.037. The CVE window: CISA's "Adds 10 Known Exploited Vulnerabilities" alert and Security Affairs' write-up shared CVE-2023-25914, 18 hours apart.
- All 41 real records from 13 sources became 38 events: 1Password (3 sources) and the CISA KEV batch (2). Known miss: SecurityWeek and The Hacker News on one Drupal flaw (similarity 0.13; only one names the CVE) stayed two events.
- CVEs are found at normalization in the headline, the whole summary (before the 300-character excerpt cut) and metadata, and stored in `source_records.cves`. Migration `004_grouping.sql` creates `pg_trgm`, makes canonical URL unique per source rather than globally, backfills CVEs of older records from headline and excerpt, and adds a trigger that refuses deletes and any change other than `event_id`.
- An event's title, `published_at` and first-seen time come from its earliest record, so an event that gains an earlier source moves down the feed. `deduplicator.move_record(conn, record_id, to_event_id=None)` moves a record to another or a new event, recomputes both events and removes an emptied one. Events already stored before #5 are not regrouped.
- The API added `source_count` and each source's `record_id`; sources are listed earliest first. The page shows "N sources" in an unstyled `<details>` listing the other sources. The browser suite now also seeds the real Security Affairs and The Hacker News captures.
- Risks: a CVE roundup (such as a KEV batch) can attract every later story naming any of its CVEs within 7 days; short generic headlines about one organization from two outlets can reach 0.2.
