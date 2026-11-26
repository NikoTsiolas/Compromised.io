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
