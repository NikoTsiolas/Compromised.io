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

## Trust labels as built, 2026-11-26
As of `NikoTsiolas/Compromised.io@025fd6b` on branch `ticket-7-trust-score` (ticket #7, built by an Opus session, CI green, not merged on this date):
- Weights: the heaviest source set the base; each other news outlet added 10 x its weight / 50; the cap of 80 without official confirmation always held; 100 and 10 were fixed. Default weights reproduced the agreed numbers exactly.
- An independent outlet was a distinct source in the registry; two records from one publisher counted once.
- "Under investigation" was set by no rule, because status never comes from content. A real candidate existed (a Flight Centre excerpt saying it "is investigating a cyber incident"). Left for Niko to decide.
- "Disputed" was set only by the headline of a press or official record published after the event's first record, containing denies/disputes/refutes within five words of breach, hack, attack, claim or similar, or "retract", "claim is false/fake/hoax", or "no evidence of a breach". No real sample came out disputed.
- Label wording named who confirmed: "the company" only when a vendor's own source covered its own organization or product; CISA read "a government agency"; other vendor posts read "security researchers"; "Flaw confirmed by ..." when the confirming record was about a flaw.
- On 36 real sample events: 16 reported by one outlet (50), 9 confirmed by security researchers (90), 6 flaw confirmed by a government agency (4 at 90, 2 at 100), 3 attacker claims (20), 1 reported by three outlets (70), 1 flaw confirmed by the company (90).
- Looked wrong: two Cisco Talos posts (a newsletter and a podcast) scored 90 as "Confirmed by security researchers" though they are not incidents; they appeared only under Research.
- The API sent label, score and source names together as one `trust` object; `GET /v1/scoring` fed the "How we score" page. Migration `007_trust_status_and_score.sql` (the redesign branch also used 007 and 008 on this date).
