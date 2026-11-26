# Trust labels and score

- 2026-11-26: Verification status comes from source tier, never from content and never from the LLM.
  - Vendor and government sources (CISA, MSRC, Talos, Unit 42, Google Threat Intelligence): officially confirmed.
  - Established press: credibly reported.
  - Ransomware.live: unverified attacker claim.
  - An event takes the strongest status among its sources.
- 2026-11-26: Two guards. A ransomware claim is upgraded only when a press or official source is merged into the same event. "Disputed or retracted" is set only by explicit retraction phrasing in a later source.
- 2026-11-26: Reader-facing labels: "Confirmed by the company", "Reported by N news outlets", "Claimed by attackers, not confirmed", "Under investigation", "Disputed". Source names stay visible.
- 2026-11-26: Niko asked for a percentage. Claude objected that a bare percentage reads as a measured probability. Agreed outcome: a 0-100 score from a fixed formula, published on a "How we score" page, always shown beside its label and sources, never alone.
- 2026-11-26: Formula as agreed:
  - Base by strongest source: attacker claim only 20; one news outlet 50; the affected company or a government agency confirms 90.
  - +10 per additional independent news outlet, capped at 80 without official confirmation.
  - Official confirmation plus press: 100.
  - Disputed or retracted: 10.
- 2026-11-26: Niko added that sources should be weighted by who is reporting, not only counted. Each source therefore carries a configurable weight in the source registry, defaulting to its tier's value.

Related: [Feed scope and sources](feed-scope-and-sources.md), [LLM usage](llm-usage.md).
