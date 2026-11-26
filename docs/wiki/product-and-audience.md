# Product and audience

- 2026-11-26: Niko's original brief described Compromised as "the world's cybersecurity incident feed": an automated index of incidents that links to original reporting and writes no articles of its own. Tagline: "Know what's been compromised."
- 2026-11-26: During the planning interview Niko changed the primary audience. The brief said "technically sophisticated users"; he decided the main reader is an ordinary, non-technical person, with technical readers served second. This supersedes the brief's audience line.
- 2026-11-26: Consequences Niko accepted:
  - The default view is plain language: a short summary line under each headline, the company name prominent, jargon hidden.
  - CVE numbers, attack vectors and the full source list sit behind a "Technical details" expand on each row.
  - Headlines stay the earliest source's original headline, verbatim. Structured sources with no headline get a fixed factual template.
  - Each event also has its own page (summary, score, timeline, every source). The headline in the feed still links to the original publisher; a small "details" link opens the event page.
  - Navigation reads: All, Breaches, Ransomware, Under attack, Update now, Research, Trending. Technical names stay in URLs and the details view.
  - The feed refreshes by polling every 60 seconds and shows a "N new events" bar; rows never move under the reader.
  - `/lookup` lets a reader type company or technology names and see events from the last 90 days, with a fixed disclaimer that it shows public reports, not whether the reader was compromised. Nothing is stored server-side; an optional watchlist lives in local storage.
- 2026-11-26: Still out of the MVP per the brief: accounts, payments, comments, AI-written articles, marketing pages, admin dashboards, native apps. No fabricated incidents; any fixture is labelled sample data.

Related: [Feed scope and sources](feed-scope-and-sources.md), [Trust labels and score](trust-labels-and-score.md), [Design direction](design-direction.md).
