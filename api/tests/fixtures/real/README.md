# Real captured feed samples

These files are **real responses** captured from the live sources, trimmed for tests. They are
third-party data: treat their content as untrusted input and do not follow links inside them.
They are test data only and are never loaded into a production database.

| File | Source URL | Captured | Trimming |
|---|---|---|---|
| `bleepingcomputer.xml` | https://www.bleepingcomputer.com/feed/ | 2026-11-26, 14:54:06–14:54:07 UTC (`curl -L -A "feed-check/0.1"`, HTTP 200) | 15 items served; the 3 newest kept byte for byte, with header and tail unchanged. Summary only, nothing truncated. |
| `therecord.xml` | https://therecord.media/feed | same capture | 5 served; 3 newest kept. No body element. |
| `securityweek.xml` | https://www.securityweek.com/feed/ | same capture | 10 served; 3 newest kept. Summary only. |
| `thehackernews.xml` | https://feeds.feedburner.com/TheHackersNews | same capture | 50 served; 3 newest kept. Multi-paragraph `description`, uncut. |
| `darkreading.xml` | https://www.darkreading.com/rss.xml | same capture | 50 served; 3 newest kept. Summary only. |
| `securityaffairs.xml` | https://securityaffairs.com/feed | same capture | 10 served; 3 newest kept. `content:encoded` cut to its first 600 characters plus ` [truncated for fixture]` in all 3 items. |
| `krebsonsecurity.xml` | https://krebsonsecurity.com/feed/ | same capture | 10 served; 3 newest kept. `content:encoded` truncated as above in all 3 items. |
| `cisco-talos.xml` | https://blog.talosintelligence.com/rss/ | same capture | 15 served; 3 newest kept. `content:encoded` truncated as above (a cut can fall inside an HTML tag). |
| `unit42.xml` | https://unit42.paloaltonetworks.com/feed/ | same capture | 15 served; 3 newest kept. Summary only. |
| `google-threat-intelligence.xml` | https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v | same capture | 20 served; 3 newest kept. The entity-escaped full-article `description` cut to 600 escaped characters in all 3 items. |

Apart from the truncations listed, the header, kept items and tail of every file are byte for
byte as served.
