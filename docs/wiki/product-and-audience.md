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

## Event pages as built, 2026-11-26
Ticket #11, built by an Opus session on branch `ticket-11-event-pages` (commit named in the merge):
- Address: `/events/<id>`, the API's event id (decision by Claude). An event keeps its id as sources join it, because grouping adds records to the existing event and only re-derives its title and times. No slug in the address, so a title that changes when an earlier source joins never changes the link.
- Regrouping: `deduplicator.move_record` deletes an event left without records; migration `010_event_redirects.sql` records where its last record went. `GET /v1/events/<old id>` answers 308 to the new event, always one hop (older redirects are moved on when their target is deleted), and the page answers 308 to `/events/<new id>`. A split that leaves the old event non-empty keeps the old address on the old event.
- `GET /v1/events/{id}` returns the feed's event shape plus `cves` (every CVE its records name, sorted); 404 for an unknown id. The list endpoint is unchanged.
- Status codes: with Cache Components a page that calls `notFound()` has already streamed a 200, and a Proxy rewrite's own status is overwritten by the page. So `web/proxy.ts` asks the API for the status first (one extra API request per page view) and either redirects (308, regrouped event) or rewrites to `/events/unknown`, a page that calls `notFound()` while it is prerendered and so is stored and served with a real 404 and `noindex`. If the API cannot be reached the page renders and says it could not load the event. Found while building: inside Proxy, cancelling a fetch body never settled, so the body is read instead.
- The page reuses the story parts (kicker, picture with publisher credit or logo tile, "AI summary", "Advice from source", trust, technical details without the source list) in one thin column. The timeline lists every source in publication order with its original time shown in the reader's zone, each linking to the publisher. The headline links to the publisher, as in the feed.
- Feed: the featured lead, the cards and the rows gained a small "Details" link (named "Details" inside the story, which is an article named by its headline); the headline still opens the publisher. Sample events on `/preview` show no link. Pictures carry a view-transition name (`event-media-<id>`) on both sides.
- Metadata from stored plain text only: title "<headline> · Compromised"; description the AI summary, else the earliest excerpt, else the trust label and sources, cut at 200 characters; Open Graph type article and a summary Twitter card, with no image (a publisher's photo is never used as a share image). Events in no feed tab (commentary, out-of-scope advisories) keep a page but are marked noindex.
