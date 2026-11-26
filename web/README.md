# Compromised web app

Next.js (App Router, TypeScript), Tailwind CSS and shadcn/ui. The page server-renders the feed
from the API at `API_URL` (default `http://127.0.0.1:8000`). Local setup is in the repository
README.

```sh
pnpm dev          # http://localhost:3000 (from the repo root, `pnpm dev` also starts the API and worker)
pnpm test:e2e     # browser seam: Playwright starts its own API and web app on ports 8100 and 3100
pnpm lint && pnpm typecheck
```

`AGENTS.md` is written by `next dev`; it points coding agents at the bundled Next.js docs.
