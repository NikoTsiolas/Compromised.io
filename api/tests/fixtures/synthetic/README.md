# Synthetic test data

Hand-written inputs for tests that need content no real capture contains (for example markup in a
headline). These are **not real captures and not real incidents**; every item says so in its
headline, and links point at `example.com`. Test data only: never loaded into production.

| File | Purpose |
|---|---|
| `text-not-markup.xml` | Browser seam: a headline with `<`, `&` and an escaped `<script>` must reach the page as text. It names a breach so that it lands in the All tab. |
| `vulnerability-gate.xml` | Pipeline, API and browser seams: flaws in products on the "people use" list (Windows, Chrome) that are exploited, critical, or neither. No real capture had one. |
| `ransomware-live-hostile.xml` | Pipeline seam: items shaped like Ransomware.live whose link or guid is an `.onion` address or an off-site "leak" page, and whose descriptions carry contact details. No leak-site or `.onion` link may be stored. |
| `msrc-sug-exploited.json` | Pipeline seam: an MSRC SUG answer (trimmed to the fields used) marking two listed-product CVEs from the real MSRC sample as exploited. No real answer had an exploited flaw in a listed product. |
| `cve-outside-window.xml` | Pipeline seam: an item naming CVE-2023-25914, dated 3 December 2026, more than 7 days after the real CISA and Security Affairs records that name it. No real capture had a shared CVE outside the window. |
| `same-canonical-url.xml` | Pipeline seam: a second source whose item links the real BleepingComputer 1Password article (with tracking parameters and a fragment) under an unrelated headline. No two real captures shared a URL. |
| `adversarial-headlines.xml` | Pipeline seam: headlines and excerpts that try to instruct the LLM enricher (set a status or score, break out of the untrusted-data wrapper, plant an action line or a link). |
| `enrichment-replies.json` | Browser seam: stand-in model replies for two synthetic items (`compromised.seed --sample-enrichment`), so the page shows an AI summary and a stated action line without calling the model. |
