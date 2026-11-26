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

## Findings from the feed capture on 2026-11-26
A subagent fetched each of the 14 endpoints once at 14:54 UTC and saved trimmed real samples as test fixtures (see [Working agreements](working-agreements.md) for the location; field-by-field notes are in `source-fields.md` beside them).
- 2026-11-26: The MSRC Update Guide RSS carries no severity or exploited field, and 979 of its 5,776 items repeat a guid (one item per revision). This settles the open question above. The MSRC SUG API (`api.msrc.microsoft.com/sug/v2.0/en-US/vulnerability`, filtered by CVE number) returned `severity` and `exploited` without a key; its rate limits are undocumented. NVD 2.0 gives only a CVSS band, at 5 requests per 30 seconds without a key. Decision by Claude: use the SUG API for Microsoft severity, queried only for entries whose product is on the curated list.
- 2026-11-26: CISA KEV fields: `vendorProject`, `product`, `dateAdded`, `requiredAction`, `dueDate`, `knownRansomwareCampaignUse`.
- 2026-11-26: Ransomware.live RSS: the victim is in the title after " : ", the group in the title and the `/group/<slug>` guid, and `pubDate` is when Ransomware.live recorded the claim. No item linked to a leak site, but descriptions contained an attacker contact email, a Session ID and victim URLs. Decision by Claude: descriptions from this source are never stored; this narrows the 300-character excerpt rule for this one source.

## Classification and scope as built, 2026-11-26
As of `NikoTsiolas/Compromised.io@e61b7a0` (ticket #6, built by an Opus subagent, CI green on that commit):
- The alias dictionary was `api/src/compromised/data/catalog.json`: 368 entries, 262 flagged as products people use, each with a logo key, plus threat actors and reporters/countries that are never treated as the affected organization. Enterprise gear was flagged as not used by ordinary people.
- Run over 41 real captured headlines: research 8, active exploitation 7, vulnerability 6, data breach 5, espionage 4, ransomware 4, other 3, malware 2, zero-day 1, supply chain 1. Six were filtered as commentary, 17 had an unknown organization, and 22 appeared in no tab.
- Known weakness: the phrase rules ignored negation ("not exploited").
- Interfaces left for later tickets: adapters fill metadata keys `victim`, `vendor`, `product`, `exploited`, `severity`; `scope.refresh_event` is called after a merge or status change; the enricher uses `scope.tabs_for` with `storage.save_classification`; source ids equal the fixture file names; `GET /v1/tabs` existed; Trending returned empty; `pnpm db:reclassify` reclassified an existing dev database.

## Fetching as built, 2026-11-26
As of `NikoTsiolas/Compromised.io@0066781` (ticket #3, built by an Opus subagent, CI green on that commit):
- All 10 RSS news and research sources had registry entries with tier, weight, interval and size cap; weight defaulted to the tier's base score (official 90, press 50, claim 20). Krebs carried a 35-second crawl delay.
- Only registry hosts over HTTPS were fetched. Redirects were followed by hand, at most three, each target re-checked; off-list, downgraded or over-limit redirects were refused.
- Connect, read and whole-attempt timeouts; a size cap on the decompressed body; retries on 429, 5xx and timeouts with doubling backoff never shorter than the crawl delay. Tested against a local HTTPS stub server in a CI step named "Fetcher seam".
- ETag and Last-Modified were stored and sent; a 304 skipped parsing. Any DOCTYPE before the root element was refused, in addition to feedparser not resolving external entities.
- `GET /v1/status` returned overall status (starting, live, degraded, down) and each source's state and last success, without error text.
- The worker derived what was due from `last_attempt_at` in the database, so a restart did not re-poll every source.
- Source ids `cisco-talos` and `google-threat-intelligence` matched the fixture names. The migration was `003_source_registry_and_health.sql`. Browser-suite ports could be overridden with `E2E_API_PORT` and `E2E_WEB_PORT`.
- A real check on this date fetched each of the 10 sources once; all succeeded (200 items). SecurityWeek's second fetch returned 304.

Friction the subagent reported: `mvp` moved twice under it and the ticket #6 merge conflicted in 8 files; the auto-mode classifier blocked running the long-lived worker loop, so real feeds were checked with one-off passes.

## Structured sources as built, 2026-11-26
As of `NikoTsiolas/Compromised.io@da2efc0` on branch `ticket-4-structured-sources` (ticket #4, built by an Opus subagent):
- The registry held all 14 sources. CISA advisories was a plain RSS source (its own headlines kept); CISA KEV, MSRC Update Guide and Ransomware.live had their own adapters (`pipeline/adapters.py`, `pipeline/msrc.py`). The four carried `backfill_days=30`: an item published more than 30 days before a fetch was never imported, on the first run or any later one (a rolling window, so the KEV catalog's 1,805 entries did not flood in on the second run).
- Fixed title templates, filled only with source fields (decision by Claude): KEV "`<vulnerabilityName>` (`<CVE>`) added to CISA's Known Exploited Vulnerabilities catalog"; MSRC "Microsoft Update Guide: `<name>` (`<CVE>`)"; Ransomware.live "`<group>` claims `<victim>` as a ransomware victim".
- Metadata keys: KEV `cve`, `vendor`, `product`, `date_added`, `due_date`, `required_action`, `known_ransomware_use`, `exploited`; MSRC `cve`, `vendor` ("Microsoft"), `product` (the SUG `tag`), `severity`, `exploited`, `revised_at`; Ransomware.live `victim`, `group`, `group_key` (guid slug, lower-cased), `country`, `attacker_claim`. KEV links pointed at the CISA catalog search for the CVE (`?search_api_fulltext=<CVE>`, not opened to check).
- Ransomware.live: description and enclosure dropped; the only link kept was one on `www.ransomware.live` (item link, else the guid's group page); an item with neither was dropped.
- MSRC: one entry per CVE, dated by its first revision in the feed, with the newest revision's date as `revised_at`. Only CVEs whose product is on the "people use" list, first published inside the window and revised since the last successful check were sent to the SUG API, 40 per request through the fetcher. An entry was stored only if Microsoft rated it Critical or reported it exploited; a stored entry whose rating changed in a later revision had its metadata replaced and `scope.refresh_event` called. A failed SUG request failed the whole MSRC poll, so its validators were not stored and the next poll retried. The SUG API shared its host with the feed (`api.msrc.microsoft.com`); it was declared as a lookup endpoint (`sources.LOOKUPS`) and added to the allow-list deliberately.
- Real check on 2026-11-26 around 17:15 UTC, each endpoint fetched once with the project's user agent: KEV 1,805 entries, 45 inside 30 days, 2 in a product people use (Google Chromium, WordPress) and so in the feed. Ransomware.live 200 items, all stored, none with a non-Ransomware.live link or an excerpt. MSRC 5,776 items, 4,116 distinct CVEs; 1,420 listed-product CVEs had a revision inside 30 days, many years old, which led to dating entries by first revision (not re-measured, to stay within the agreed request budget). SUG was asked about 3 CVEs: an Excel CVE rated Critical (stored), an Edge pickup with no severity, a Mariner entry rated "None".
- CISA advisories answered HTTP 403 to the project's user agent (`CompromisedBot/0.1 (+https://github.com/NikoTsiolas/Compromised.io)`), while the KEV file on the same host answered 200 and the research capture with `feed-check/0.1` had succeeded. Not retried. Open: whether to change the user agent for this source.
