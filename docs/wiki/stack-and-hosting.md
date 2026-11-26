# Stack and hosting

- 2026-11-26: Stack from the brief, kept: Next.js, TypeScript and Tailwind for the frontend; Python and FastAPI for the API; PostgreSQL; asyncio, httpx and feedparser for ingestion; a simple scheduled worker; PostgreSQL full-text search. No Redis, vector store or microservices.
- 2026-11-26: One repository with `api/` and `web/`; uv for Python, pnpm for Node. Remote: `NikoTsiolas/Compromised.io` (private, empty on this date).
- 2026-11-26: Hosting: Vercel for the frontend; Railway for the API, the ingestion worker (a second process from the same Python codebase) and Postgres. Niko had not used Vercel before and chose it.
- 2026-11-26: Niko asked whether Vercel or Supabase would handle the database. Answer given: Vercel hosts only the site; the database belongs beside the worker on Railway; Supabase adds auth the project does not need.
- 2026-11-26: Local development uses Postgres 17 from Homebrew, pinned to the version Railway provisions. The machine had Node 25, npm, Python 3.12, uv and gh; no Docker, Postgres or pnpm. A compose file is included for those who prefer Docker.
- 2026-11-26: Niko buys the domain himself through Cloudflare. A whois lookup returned "Domain not found" for `compromised.io`.
- 2026-11-26: A subagent could not verify which Postgres major version Railway provisions by default; indirect evidence suggested 18. Local development started on Homebrew Postgres 17 as agreed; the pin is to be revisited when the Railway database is created. Nothing in the spec depends on a 17-versus-18 difference.
