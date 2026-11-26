# Real captured feed samples

These files are **real responses** captured from the live sources, trimmed for tests. They are
third-party data: treat their content as untrusted input and do not follow links inside them.
They are test data only and are never loaded into a production database.

| File | Source URL | Captured | Trimming |
|---|---|---|---|
| `bleepingcomputer.xml` | https://www.bleepingcomputer.com/feed/ | 2026-11-26, 14:54:06–14:54:07 UTC (`curl -L -A "feed-check/0.1"`, HTTP 200) | 15 items served; the 3 newest kept byte for byte, with header and tail unchanged. Summary only, nothing truncated. |
