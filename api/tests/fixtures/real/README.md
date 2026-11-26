# Real captured feed samples

These files are **real responses** captured from the live sources, trimmed for tests. They are
third-party data: treat their content as untrusted input and do not follow links inside them.
They are test data only and are never loaded into a production database.

| File | Source URL | Captured | Trimming |
|---|---|---|---|
| `bleepingcomputer.xml` | https://www.bleepingcomputer.com/feed/ | 2026-11-26, 14:54:06–14:54:07 UTC (`curl -L -A "feed-check/0.1"`, HTTP 200) | 15 items served; the 3 newest kept byte for byte, with header and tail unchanged. Summary only, nothing truncated. |

The files below come from the same capture (all 14 sources requested in parallel between
14:54:06 and 14:54:07 UTC on 2026-11-26, `curl -L --max-time 60 -A "feed-check/0.1"`, every
response HTTP 200). Each file's name is the source id used in the tests. Headers, kept items and
tails are byte for byte as served, except that some full-text bodies were cut to their first 600
characters and end in ` [truncated for fixture]`.

| File | Source URL | Items served | Kept | Truncation |
|---|---|---|---|---|
| `therecord.xml` | https://therecord.media/feed | 5 | 3 newest | none (no body element) |
| `securityweek.xml` | https://www.securityweek.com/feed/ | 10 | 3 newest | none |
| `thehackernews.xml` | https://feeds.feedburner.com/TheHackersNews | 50 | 3 newest | none |
| `darkreading.xml` | https://www.darkreading.com/rss.xml | 50 | 3 newest | none |
| `securityaffairs.xml` | https://securityaffairs.com/feed | 10 | 3 newest | `content:encoded` in all 3 |
| `krebsonsecurity.xml` | https://krebsonsecurity.com/feed/ | 10 | 3 newest | `content:encoded` in all 3 |
| `cisa-advisories.xml` | https://www.cisa.gov/cybersecurity-advisories/all.xml | 30 | 3 newest | `description` in all 3 (entity-escaped; cut moved back before a split entity) |
| `cisco-talos.xml` | https://blog.talosintelligence.com/rss/ | 15 | 3 newest | `content:encoded` in all 3 |
| `unit42.xml` | https://unit42.paloaltonetworks.com/feed/ | 15 | 3 newest | none |
| `google-threat-intelligence.xml` | https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v | 20 | 3 newest | `description` in all 3 |
| `ransomware-live.xml` | https://www.ransomware.live/rss.xml | 200 | 3 newest | none |
| `msrc-update-guide.xml` | https://api.msrc.microsoft.com/update-guide/rss | 5,776 | 5 newest | none (keeps its UTF-8 BOM) |
| `cisa-kev.json` | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | 1,805 entries | 3 most recently added | none; top-level `count` still says 1805 |

`cisa-kev-wordpress.json` holds one real KEV entry that the trimmed `cisa-kev.json` does not:
CVE-2026-119977, vendor `WordPress`, product `WordPress Core`, whose CISA name repeats the
vendor. It is not a byte-for-byte capture. It was rebuilt on 2026-11-26 from the source record
the project's fetcher stored from the live catalog that day (13:24 US Eastern, in a local
development database), with only the fields the KEV adapter reads, each value unchanged:
`cveID`, `vendorProject`, `product`, `vulnerabilityName` (the stored title minus the template's
suffix), `dateAdded`, `shortDescription`, `requiredAction`, `dueDate`,
`knownRansomwareCampaignUse`. `notes`, `cwes` and `forensicTriage` were not stored and are absent.

`securityaffairs-switzerland.xml` comes from a later capture of https://securityaffairs.com/feed
(2026-11-26, served 20:40:02 UTC, `curl -A "Compromised/0.1 (+https://github.com/NikoTsiolas/Compromised.io)"`,
HTTP 200, 10 items). It keeps one item, "Switzerland Confirms First AI-Agent Cyberattacks on Local
Organisations" (25 Nov 2026), with the feed's header and tail byte for byte; its `content:encoded`
is cut to its first 600 characters and ends in ` [truncated for fixture]`. It is the story whose
"Switzerland" tag made a country the affected organization.

Ransomware.live items are attacker claims relayed by a third party; their descriptions are
attacker-supplied text. None of the 3 kept items links to a leak site or `.onion` address.

## MSRC SUG API answers

Microsoft's own severity and exploited flag for MSRC Update Guide entries (the feed carries
neither). Both are real, unmodified responses from
`https://api.msrc.microsoft.com/sug/v2.0/en-US/vulnerability`, filtered with OData `$filter`.

| File | Filter | Captured | Notes |
|---|---|---|---|
| `msrc-sug.json` | `cveNumber eq 'CVE-2026-112732' or cveNumber eq 'CVE-2026-69291' or cveNumber eq 'CVE-2026-72965'` | 2026-11-26, 17:07:10 UTC (`curl -A "feed-check/0.1"`, HTTP 200, 10,226 bytes) | The three entries in `msrc-update-guide.xml` whose product is on the "people use" list. Visio: `Critical`; both Windows flaws: `Important`; none exploited. |
| `msrc-sug-CVE-2026-70197.json` | `cveNumber eq 'CVE-2026-70197'` | 2026-11-26, during the feed research (HTTP 200, 6.3 KB) | A .NET CVE not in the trimmed feed sample: `Important`, not exploited. |
