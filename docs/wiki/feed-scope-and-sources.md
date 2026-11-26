# Feed scope and sources

## Scope
- 2026-11-26: Niko: "I don't want this to be a threat feed." The main feed shows only things a person could be affected by: breaches, confirmed ransomware attacks, leaks, and exploited or critical flaws in widely used products.
- 2026-11-26: "All events" requires a named affected organization or product. Threat research, malware analysis and espionage reports go under Research. Attacker claims with no other coverage stay under Ransomware, labelled as claims, and out of the main feed.
- 2026-11-26: A CVE appears only when it affects a product on a curated list of things people use (Windows, iPhone, Android, Chrome, routers, popular apps) and is rated critical or is being exploited. CVE rows carry the product's logo and a plain-language line.
- 2026-11-26: GitHub Security Advisories were dropped from the MVP (library flaws mean nothing to the audience).
- 2026-11-26: Niko raised fetching ransomware gangs' .onion sites or X accounts directly. Decided against: attacker claims come only through Ransomware.live, and the site never fetches or links to leak sites. Reasons: Ransomware.live already monitors them; it would mean running Tor against criminal infrastructure, which the brief forbids; the pages host stolen personal data; X's API is paid.
- 2026-11-26: Entity extraction is deterministic: structured fields where a source provides them, plus a curated alias dictionary of vendors and products matched against headlines; otherwise "unknown". The LLM also proposes an organization (see [LLM usage](llm-usage.md)).
- 2026-11-26: Stored per source record: headline, link, timestamps, extracted metadata, and a plain-text excerpt capped near 300 characters. Full feed text is discarded at ingestion.
- 2026-11-26: First run backfills 30 days from structured sources plus whatever each news feed holds; everything is kept from then on.

## Sources verified on 2026-11-26
A subagent fetched each endpoint around 14:30 UTC with a generic user agent. No bot blocking was seen. Publishers' terms pages were not read, except Ransomware.live's.

| Source | Endpoint | Agreed interval | Notes |
|---|---|---|---|
| The Record | `https://therecord.media/feed` | 5 min | Only 5 items per fetch; no conditional GET |
| BleepingComputer | `https://www.bleepingcomputer.com/feed/` | 10 min | 304 via Last-Modified |
| SecurityWeek | `https://www.securityweek.com/feed/` | 10 min | ETag + Last-Modified |
| The Hacker News | `https://feeds.feedburner.com/TheHackersNews` | 15 min | No conditional GET |
| Dark Reading | `https://www.darkreading.com/rss.xml` | 15 min | No conditional GET |
| Security Affairs | `https://securityaffairs.com/feed` | 15 min | Full text in feed; excerpt only |
| Krebs on Security | `https://krebsonsecurity.com/feed/` | 30 min | Crawl-Delay 35; full text in feed |
| CISA advisories | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | 30 min | 390 KB per fetch |
| Cisco Talos | `https://blog.talosintelligence.com/rss/` | 30 min | 1.1 MB; ETag |
| Unit 42 | `https://unit42.paloaltonetworks.com/feed/` | 30 min | ETag + Last-Modified |
| Ransomware.live | `https://www.ransomware.live/rss.xml` | 30 min | 200 items; Crawl-delay 5 |
| CISA KEV | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | 60 min | 1.9 MB; ETag |
| MSRC Update Guide | `https://api.msrc.microsoft.com/update-guide/rss` | 60 min | 3.3 MB, ~5,776 entries; filtered by the CVE rule above |
| Google Threat Intelligence | `https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v` | 60 min | Replaces Google TAG |

- 2026-11-26: The MSRC blog had no RSS feed; the Update Guide feed replaces it. The CVRF API was skipped (monthly documents ~33 MB).
- 2026-11-26: The Google TAG feed returned 404; Google Threat Intelligence replaces it under its real name.
- 2026-11-26: Ransomware.live's documented v2 API returned 404 on every endpoint tried; the PRO API needs a key. Its terms say personal, non-commercial use only. Niko accepted keeping Compromised non-commercial while this source is used. A PRO key, if he requests one, would be an optional environment variable.
- 2026-11-26: All intervals are configurable per source; conditional GET is used wherever supported.
- 2026-11-26: Open at time of writing: whether the MSRC feed states severity per entry. If not, severity comes from the public NVD database.
