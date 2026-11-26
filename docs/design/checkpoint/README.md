# Design checkpoint: tickets #10, #11, #15 and #16 merged

Screenshots taken on 2026-11-26 from a production build (`SAMPLE_PREVIEW=1`) of branch
`merge-tickets-10-11-15-16`, as a reader in London sees them, with reduced motion. The two-tab
layout of #16 with the other three tickets carried into it: **Featured** (`/`) and the **Feed**
(`/feed`) with the real widget figures of #15 (also behind the phone tab bar's Charts), Trending
switched on in the Feed and the real **search** page of #10 (reached from the header and the
tab bar's Search), and one **event page** of #11 (`/events/4`, the 1Password event three outlets
reported), linked from Featured's lead, cards and list and from the Feed's open Details panel.

The real pages are a fresh database filled on that date by one fetch of every feed in the
registry (Security Affairs from a capture made minutes earlier, so it was not fetched twice;
The Hacker News and Google Threat Intelligence unreachable from this machine's DNS; CISA
advisories 403; MSRC 400, issue #17), the CISA KEV catalog (1,805 entries), and two article-preview
passes for Security Affairs and BleepingComputer (five pages each). The search images show
`/search?q=breach`, which includes incidents kept out of every tab, each marked "Not shown in the
feed". The sample-data routes (`/preview`, `/preview/feed`) show the same components with
invented values under their banner; search and event pages have no sample route.

| | Light | Dark | Phone light | Phone dark | Tablet light | Tablet dark |
|---|---|---|---|---|---|---|
| Featured, real (`/`) | [featured-light](featured-light.png) | [featured-dark](featured-dark.png) | [featured-phone-light](featured-phone-light.png) | [featured-phone-dark](featured-phone-dark.png) | [featured-tablet-light](featured-tablet-light.png) | [featured-tablet-dark](featured-tablet-dark.png) |
| Feed, real (`/feed`) | [feed-light](feed-light.png) | [feed-dark](feed-dark.png) | [feed-phone-light](feed-phone-light.png) | [feed-phone-dark](feed-phone-dark.png) | [feed-tablet-light](feed-tablet-light.png) | [feed-tablet-dark](feed-tablet-dark.png) |
| Search, real (`/search?q=breach`) | [search-light](search-light.png) | [search-dark](search-dark.png) | [search-phone-light](search-phone-light.png) | [search-phone-dark](search-phone-dark.png) | [search-tablet-light](search-tablet-light.png) | [search-tablet-dark](search-tablet-dark.png) |
| Event page, real (`/events/4`) | [event-light](event-light.png) | [event-dark](event-dark.png) | [event-phone-light](event-phone-light.png) | [event-phone-dark](event-phone-dark.png) | [event-tablet-light](event-tablet-light.png) | [event-tablet-dark](event-tablet-dark.png) |
| Featured, sample (`/preview`) | [sample-featured-light](sample-featured-light.png) | [sample-featured-dark](sample-featured-dark.png) | [sample-featured-phone-light](sample-featured-phone-light.png) | [sample-featured-phone-dark](sample-featured-phone-dark.png) | [sample-featured-tablet-light](sample-featured-tablet-light.png) | [sample-featured-tablet-dark](sample-featured-tablet-dark.png) |
| Feed, sample (`/preview/feed`) | [sample-feed-light](sample-feed-light.png) | [sample-feed-dark](sample-feed-dark.png) | [sample-feed-phone-light](sample-feed-phone-light.png) | [sample-feed-phone-dark](sample-feed-phone-dark.png) | [sample-feed-tablet-light](sample-feed-tablet-light.png) | [sample-feed-tablet-dark](sample-feed-tablet-dark.png) |

Desktop 1440px, phone 390px at 2x, tablet 820px, full page. In each Featured and Feed image the
first story's technical details are open (in the Feed the open panel also shows "Open the event
page"). To regenerate: run a web build with `SAMPLE_PREVIEW=1` against an API with real events,
then

    BASE_URL=http://localhost:3000 EVENT_PATH=/events/<id> SEARCH_PATH="/search?q=breach" \
      node web/scripts/capture-checkpoint.mjs

What the real pages show on this date: 10 events on the All tab, 3 with a publisher photo
(Security Affairs' Flight Centre, BleepingComputer's 1Password, The Record's FIFA) and 7 tiles.
Dark Reading's two All-tab stories (.NET, Binance) show tiles: its images are off by default in
the registry since this merge, because its stock photos include the banned hooded-figure
imagery. "Most reported organisations" lists Flight Centre, 1Password, FIFA, .NET and Inception;
no country appears any more (Security Affairs' Switzerland story now has an unknown
organisation). The widget images of #15 below (`widgets-*.png`) were not regenerated.

## Earlier: Featured and Feed (ticket #16)

The images this section names were replaced by the merged set above on 2026-11-26.

Screenshots for the owner's sign-off, taken on 2026-11-26 from a production build
(`SAMPLE_PREVIEW=1`), as a reader in London sees them, with reduced motion so nothing is caught
mid-animation. **Featured** (`/`) keeps the image-led, news-style page; the **Feed** (`/feed`) is
the social-style tab: Option A's timeline posts inside Option C's three-column shell, from the
Figma file https://www.figma.com/design/plOOtLTSKg9RuAphEHP3CM (exports on branch
`claude/figma-feed-options-8b9aa8`, `docs/design/social-options/`).

The real tabs are a database filled by one fetch of every feed on that date (The Hacker News and
Google Threat Intelligence unreachable from this machine's DNS; CISA advisories and MSRC
failing), with article previews from the earlier rounds. The sample-data routes (`/preview`,
`/preview/feed`) show the same components with invented values under their banner.

| | Light | Dark | Phone light | Phone dark | Tablet light | Tablet dark |
|---|---|---|---|---|---|---|
| Featured, real (`/`) | [featured-light](featured-light.png) | [featured-dark](featured-dark.png) | [featured-phone-light](featured-phone-light.png) | [featured-phone-dark](featured-phone-dark.png) | [featured-tablet-light](featured-tablet-light.png) | [featured-tablet-dark](featured-tablet-dark.png) |
| Feed, real (`/feed`) | [feed-light](feed-light.png) | [feed-dark](feed-dark.png) | [feed-phone-light](feed-phone-light.png) | [feed-phone-dark](feed-phone-dark.png) | [feed-tablet-light](feed-tablet-light.png) | [feed-tablet-dark](feed-tablet-dark.png) |
| Featured, sample (`/preview`) | [sample-featured-light](sample-featured-light.png) | [sample-featured-dark](sample-featured-dark.png) | [sample-featured-phone-light](sample-featured-phone-light.png) | [sample-featured-phone-dark](sample-featured-phone-dark.png) | [sample-featured-tablet-light](sample-featured-tablet-light.png) | [sample-featured-tablet-dark](sample-featured-tablet-dark.png) |
| Feed, sample (`/preview/feed`) | [sample-feed-light](sample-feed-light.png) | [sample-feed-dark](sample-feed-dark.png) | [sample-feed-phone-light](sample-feed-phone-light.png) | [sample-feed-phone-dark](sample-feed-phone-dark.png) | [sample-feed-tablet-light](sample-feed-tablet-light.png) | [sample-feed-tablet-dark](sample-feed-tablet-dark.png) |

Desktop 1440px, phone 390px at 2x, tablet 820px. In each image the first story's technical
details are open. The images are full-page, so the phone and tablet tab bar sits at the very
bottom of the image (on a device it floats at the bottom of the screen). To regenerate: run a
web build with `SAMPLE_PREVIEW=1` against an API with real events, then
`BASE_URL=http://localhost:3000 node web/scripts/capture-checkpoint.mjs`.

### Photos on the real Feed

All 11 posts on the All tab have a picture at the same 16:9 size: **6 publisher photos** and
**5 tiles** (4 lettermarks for three SecurityWeek stories and one Security Affairs story with no
usable picture, and 1 WordPress logo for a CISA KEV flaw). Counted in a browser with every
picture loaded. One of the photos is Dark Reading's hooded figure, noted in the #9 round; the
existing `PUBLISHER_IMAGES_OFF_FOR=darkreading` switch removes it.

## What was built from which option

| Part | Source | Notes |
|---|---|---|
| Post anatomy | **A** (Figma node 6:88) | Company avatar (logo or lettermark, 40px, the company's tile tint), company · category · local time on one line, verbatim headline linking to the publisher, labelled AI summary (or the publisher's excerpt, unlabelled, clamped to five lines), "Advice from source" box, the picture (16:9, 12px corners as in A), trust label and score on one row with the sources beneath, quiet action row. Open timeline with hairlines between posts, not C's bordered cards. |
| Trust | **A** | A's label-left, score-right row. C's trust strip with a score bar was not used: a bar makes the score read as a measured quantity, which the trust page warns against. |
| Action row | **A** | Outlet count, Details (opens the technical details in place, above the row; `eventHref` is ready for the event page), Share, Watch. Nothing else; tests check no engagement words appear. |
| Watch on phones | **C** | On phones Watch moves into the post header as a pill (where C, after Reddit's "Join", puts it), so the action row fits one line. Desktop and tablet keep A's quiet Watch in the row. |
| Shell | **C** | Desktop: categories (with icons) and Watching on the left, posts in the middle (600px), the widgets on the right. Tablet: left column and posts; widgets behind the tab bar's Charts. Phone: categories as a sideways-scrolling row; Featured, Feed, Search, Watching and Charts in the bottom tab bar. |
| Attacker claims | both | Never a photo (one shared rule for both tabs, `storyImage`), always the tile; the red label stays as before. C's pale-red claim strip was not used (it relied on the score bar). |
| New-events control | fixed | The Figma pill sat on the first headline. Here it is the existing bar in its own reserved 44px slot above the posts: it covers nothing at rest and rows never move until it is pressed (browser test). |
| Featured | unchanged look | Lead, three cards, up to six further stories, the widget rail. The category tabs moved to the Feed; a link leads to the Feed for every event. |
| Sources named once | both tabs | The trust line names the sources; the separate "+N sources" line is gone. Stories with no trust (commentary) name their publishers once instead. |

Search and Trending belong to #10: Trending in the Feed and the tab bar's Search led to a quiet
"coming soon" (`/search` was a placeholder page). Both were replaced by #10's at the merge above.

## Measured

Layout shift while loading and scrolling to the end (`web/e2e/smooth.spec.ts`, three runs):
**Featured 0.0006 to 0.0035 on desktop, 0.0000 on a phone; Feed 0.0006 to 0.0035 on desktop,
0.0000 on a phone.** "Good" is under 0.1; the suite fails above 0.02.

Contrast: every text node on the Feed is measured against its real background in the browser, in
both themes, by `web/e2e/feed-tab.spec.ts` (all at least 4.5:1). The token pairs from
`node web/scripts/contrast.mjs`, including the new ones:

| Pair | Use | Light | Dark | Needs |
|---|---|---|---|---|
| `c-ink-2` on `c-bg` | Post action row | 11.40:1 | 10.51:1 | 4.5:1 |
| `c-ink` on the tab bar (9% ink over the page) | Tab bar icons | 15.70:1 | 12.88:1 | 4.5:1 |
| `c-ink` on `c-bg` | Tab bar: chosen item's name | 18.88:1 | 15.85:1 | 4.5:1 |
| `c-ink` on `c-surface` | Watch pill, nav highlight, advice box | 17.60:1 | 14.62:1 | 4.5:1 |
| `c-ink-3` on `c-surface` | Advice label, details terms | 5.85:1 | 5.97:1 | 4.5:1 |
| `c-bg` on `c-ink` | "Link copied" pill | 18.88:1 | 15.85:1 | 4.5:1 |

The earlier pairs (headlines, metadata, accent, tiles, image credit) are unchanged and listed
in the #9 section below.

## References used

Figma MCP: `get_metadata` on the Option A page (frame sizes: post padding 16/20, 40px avatar, 12px
gap, 508x286 photo, 28px between actions) and `get_design_context` on the Northwind post (6:88)
for type sizes and the Trust component's description. Roboto in the file stands in for
Helvetica Neue; the site keeps its system Helvetica Neue stack.

Mobbin (`search_screens`, 2026-11-26), beyond the options README's references:

| Where | Reference |
|---|---|
| Share falls back to "Link copied" confirmation in place | Calm web share: https://mobbin.com/screens/50c8a2bc-4ca9-454c-a7e5-fb2c5d52c85e; Sprig "Copied!": https://mobbin.com/screens/80f61083-f31e-4a08-841f-399708c6986e |
| Bottom tab bar with a card in the feed | Bluesky: https://mobbin.com/screens/fbf2ae20-3add-4b69-815f-a5a7a15a1a9b |
| Three-column shell, left navigation | X web: https://mobbin.com/screens/fc04d864-4483-460a-bc35-0cdc61af6c89; Reddit web: https://mobbin.com/screens/fd41c55a-317e-46b3-a989-39edf3a0e088 |
| Watch in the card header on phones | Reddit community feed: https://mobbin.com/screens/feaeb88e-00f8-4472-8c41-f5da2b07abfa |

Bencho blocks (`get_block`, licences as in `web/components/bencho-pro/README.md`):

| Block | Licence | Used for |
|---|---|---|
| Tab bar (`tab-bar`) | Pro | Phone and tablet bottom bar, as links (`bencho-pro/bottom-tab-bar.tsx`) |
| Liquid tooltip (`glide-tip`) | Pro | The "Link copied" pill that grows out of Share (`bencho-pro/glide-tip.tsx`) |
| Load cards (`load-cards`) | Pro | The Feed's post-shaped loading skeleton (`bencho-pro/feed-skeleton.tsx`) |
| Pull to refresh (`pull`) | MIT | Read and **not used**: on phones it fights the browser's own pull-to-refresh, and the new-events bar already brings new posts in without moving rows under the reader. |
| Notify widget, FAQ accordion, Text fade, Image shimmer, Reorder list, Theme switch, Stacked bars | as before | Reused unchanged: new-events bar, Details opening, arriving headlines, picture loading, widget rail (its side switch is off in the Feed), theme switch, chart. |

shadcn/ui: `collapsible` (Details), `toggle` (Watch, `aria-pressed`), `tabs` (the phone category
row), `empty` (empty and coming-soon states), `aspect-ratio` (every picture and tile), `card`
(widgets), `badge` (trust). Lucide icons.

## Earlier: homepage design checkpoint (ticket #9), white and smooth revision

## Widgets with real figures (ticket #15), 2026-11-26

`widgets-light.png` (desktop, 1440 wide, full page), `widgets-spike-hover-light.png` (desktop,
pointer on September 2026) and `widgets-phone-light.png` (iPhone 13, full page): the real
homepage from a development server against a database filled by one fetch of 13 feeds on
2026-11-26 (Google Threat Intelligence unreachable, CISA advisories 403, MSRC 400) and the CISA
KEV catalog fetched once that day (version 2026.11.25, 1,805 entries). The chart shows 341 flaws
in 12 months with September (43) and November (39) as spike months; recently exploited lists
Chrome, WordPress, Windows, Chrome, Windows; most reported organisations counts All-tab events
over 30 days. Times are London time, light theme.

**Screenshots replaced on 2026-11-26 after merging #7 (trust labels) with #9.** Every row now
shows the API's own trust label, its 0-100 score and the sources it counted, in the designed
trust line (status square, label, score, "Sources: ..."); commentary carries none. The real feed
in these images is a production build against a database seeded from every real captured sample
in `api/tests/fixtures/real` (no live fetch), so the All tab holds 5 events: "Reported by N news
outlets" (50, 70) and a CISA KEV flaw "Flaw confirmed by a government agency" (90). The sample
preview uses only labels the API can produce. The dark images were previously identical to the
light ones (the site ignores the system setting); the capture script now chooses dark as the
theme switch does. The text below describes the earlier capture.

Screenshots for the owner's sign-off, taken on 2026-11-26 from a production build, light first, as
a reader in London sees them (times are the reader's local time). This revision follows Niko's
second review: article preview images, a white page, and everything smooth.

The real feed is a fresh database filled by one more fetch of every feed on that date (after
tickets #4, #5 and #8 were merged), with article previews asked politely: at most six article
pages per publisher in all, never the same page twice. The Hacker News and Google Threat
Intelligence refused the connection, CISA's advisories answered 403 and MSRC 400; none was
retried. 11 events are on the All tab. The sample-data preview (`/preview`) shows the same
components with every field and widget filled by invented values under its banner.

### Photos on the real feed (All tab, first page, loaded in a browser)

| Publisher of the event's earliest source | Rows with a photo |
|---|---|
| Security Affairs | 2 of 3 |
| Dark Reading | 2 of 2 |
| BleepingComputer | 1 of 1 |
| The Record | 1 of 1 |
| SecurityWeek | 0 of 3 (all six article pages refused the fetch) |
| CISA Known Exploited Vulnerabilities | 0 of 1 (structured source, never fetched) |
| **All** | **6 of 11**, none broken |

The article-preview pass on that date: BleepingComputer 6 of 6 pages had a preview, Security
Affairs 6 of 6, The Record 5 of 5, Krebs on Security 0 of 6 (no og:image or twitter:image on its
pages), SecurityWeek 0 of 6 (every page fetch failed), Dark Reading 0 of 1 (failed; its feed
already carries pictures). Cisco Talos and Unit 42 put pictures in their feeds.

(The images this section describes were replaced on 2026-11-26 by the #16 set above.)

### What changed in the second review

| Asked for | What the page does now |
|---|---|
| "yea fetch them" (article preview images) | For a stored record with no feed picture, the worker asks the article page once, ever, for its `og:image` (else `twitter:image`), only on hosts the registry declares as that publisher's article hosts (`Source.article_hosts`; never a feed host such as feedburner, never inferred from feed content; CISA KEV, MSRC and Ransomware.live have none). Through the hardened fetcher: allow-list and re-checked redirects, timeouts, one attempt, only the document head read (256 KB at most), robots.txt honoured, at least the crawl delay (2 s minimum) between pages of one publisher, five pages per publisher per pass. Parsed with Python's HTML parser; nothing is executed. Only https addresses are kept; our server never requests the picture. The outcome is stored in `article_previews`, apart from the record, which stays as fetched. Feed pictures offered over http (The Record) are stored in their https form. |
| A switch per source | `Source.publisher_images` in the registry and `PUBLISHER_IMAGES_OFF_FOR=darkreading,...` at run time, beside `PUBLISHER_IMAGES=off` for everything. All on by default. |
| Featured story prefers a picture | The newest named, unclaimed event leads unless an event with a picture is at most 24 hours older, which then leads instead, so a picture never lets old news displace today's. |
| "the website should be white" | Pure white ground, with dividers, tile grounds and the muted red re-tuned and re-measured below. Light is the default for every visitor whatever their system setting; dark stays behind the toggle. |
| "everything very smooth" | One set of motion tokens (`--motion-fast` 140 ms, `--motion-base` 220 ms, `--motion-slow` 320 ms, one ease-out curve). Pictures fade in over a box reserved by its aspect ratio, with a quiet shimmer while they load. Hover and focus ease; headline underlines fade in. The tab underline slides from tab to tab. Technical details and newly loaded rows open to their height. Widgets glide out of the way while one is dragged. Switching the rail's side and switching tabs are view transitions; the masthead holds still. The loading skeleton has the final layout's boxes. Everything is off under reduced motion. |

Cumulative layout shift on the homepage, measured by the browser suite (`web/e2e/smooth.spec.ts`)
while the page loads and is scrolled to the end: **0.0005 to 0.0026 on desktop** (1280x720) and
**0.0000 on a phone** (390x844), across repeated runs. "Good" is under 0.1.

Content security policy (a header from `web/next.config.ts`; nonces are not possible with partial
prerendering): `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'
'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; object-src
'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests`,
plus `Referrer-Policy: no-referrer`. Pictures may come from any https host a publisher names, and
from nothing over plain http. Development adds `'unsafe-eval'` and websocket connections for
hot reload.

Pictures that look off-brand on this date: Dark Reading's picture for the .NET story is a hooded
figure in front of green code (exactly the banned imagery), and BleepingComputer's 1Password
picture is a red "digital code" illustration (borderline). Both sources stay on by default, as
asked; `PUBLISHER_IMAGES_OFF_FOR=darkreading` would remove Dark Reading's.

### What changed against the owner's first review

| Asked for | What the page does now |
|---|---|
| "More image esque", similar to Perplexity Discover | A featured section: one lead story with a large picture, headline, summary, published time and source count, then a row of three picture cards; below them the feed, every row with a picture. |
| Pictures | The image a publisher put in its own feed (`media:content`, `media:thumbnail` or an image enclosure), https only, loaded by the reader's browser straight from the publisher with no referrer, credited on the picture ("Image: Dark Reading"). Never downloaded, proxied or cached by us; `PUBLISHER_IMAGES=off` removes them everywhere. Ransomware.live's images are never kept. Every other event, and any picture that fails to load, gets a designed tile: the company's Simple Icons logo where the catalog's logo key resolves, else a lettermark, on one of five restrained grounds picked by the company's name. |
| Featured story chosen by rule | The newest event with a named organisation that is not an attacker claim (`web/lib/featured.ts`), with the "most independent sources in 24 hours, confirmed or credibly reported" rule already written behind one switch for when source counts and trust status arrive. |
| Widgets beside the feed that the reader can move | A rail of four widgets: exploited flaws by month, recently exploited, most reported organisations, source status. Drag a widget by its handle, or focus the handle and use the arrow keys, Home and End (announced to screen readers); "Move widgets to the left/right" switches the side. Kept in local storage, applied before first paint, and the page works when storage is refused. On phones and tablets the widgets stack below the featured stories and are not draggable. |
| A chart of exploitation over the months with spikes highlighted | Columns per month in a recessive grey; spike months (at least one standard deviation above the monthly average) in the muted red with their value printed above. Hover or keyboard focus rings the month, steps the others back and shows a tooltip with the count and, for a spike, notable incidents. One tab stop, arrow keys between months, and a table for screen readers. The component is designed for three views (frequency, by sector, service outages); only frequency renders until the other two are confirmed. |
| Bencho "Text fade" as the vibe for how text appears | Used on the lead headline and summary on load, and on headlines of events that arrive after the reader presses the new-events bar. Nothing else fades. Off under reduced motion. |
| Local time instead of UTC | Every time is in the reader's zone. The server renders a UTC fallback and the browser replaces it after hydration, with no hydration mismatch. |

Kept from the first design: Helvetica Neue through the system stack, monospace for times and
identifiers, near-black and off-white with the muted red accent, the trust label and 0-100 score
always together with the source names, the "AI summary" label, "Advice from source", the
Technical details expand, the new-events bar with rows that never move, light and dark themes.

### What the real feed shows today

Widgets other than source status have no API yet (issue #15). On the real page they say so
quietly ("No figures yet", "Nothing listed yet") and show no invented values. Fields later tickets
fill keep their quiet empty states: the publisher's own excerpt (unlabelled) instead of an AI summary, "+N sources" omitted until
grouping (#5).

Note for the owner: a publisher's picture is the publisher's choice. Some use exactly the imagery
the brief bans (on this date Dark Reading's picture for the .NET story is a hooded figure in front
of green code). The switch above turns all publisher pictures off if that is not acceptable.

### Mobbin references used

Searched with the Mobbin MCP on 2026-11-26 (`search_screens`, web and iOS).

| Where | Reference |
|---|---|
| Overall layout: lead story text beside a large picture, a row of three picture cards, then larger rows with the picture on the left; a widget rail on the right | Perplexity Discover (web): https://mobbin.com/screens/ec59e633-ba10-46a5-9277-363061007f02, https://mobbin.com/screens/c40ed5d6-e417-4bf6-9d84-89b6b46ff08f, https://mobbin.com/screens/7028c676-1d3b-44e1-b1cd-290407e9b7a8, https://mobbin.com/screens/14c9db17-6526-4c8f-a166-1e24309acafd, https://mobbin.com/screens/423c2053-3a7f-4e84-ac8a-0723f1790a45 |
| "Published 9 hours ago" line and source count under the lead headline | Perplexity Discover, same screens |
| Image credit chip on the picture | Perplexity article page: https://mobbin.com/screens/626cd530-7a9d-4b33-8e12-70b356083244 |
| Phone: picture above the lead headline, smaller pictures beside headlines below | Perplexity iOS Discover: https://mobbin.com/screens/cbca6cd0-2be2-4b07-b4a0-049a259ea642; Apple News: https://mobbin.com/screens/9d5426c7-3903-4c59-acfb-b5931592f42c |
| Widgets the reader rearranges by dragging | Evernote "Customize your Home": https://mobbin.com/screens/c3ebaee2-159b-4cb8-96ff-856640b7a041; Xero business overview: https://mobbin.com/screens/c86d6e12-6b97-47de-b96b-33e24d57e1fe |
| White editorial ground, pictures beside headlines, hairlines between stories (second review) | Quartz: https://mobbin.com/screens/f4c1e482-190b-41f3-ac26-832048c1d524; The New York Times: https://mobbin.com/screens/ec249545-a287-4da4-885d-2ad20ae9b0c4; Perplexity Discover: https://mobbin.com/screens/423c2053-3a7f-4e84-ac8a-0723f1790a45 |
| Kept from the first round: underline tabs, mono times, red only for LIVE and claims, plain-words reliability label | NYT, T1 Energy, Substack, Fey (links in the research notes) |

### Bencho blocks used

Fetched with the Bencho MCP's `get_block`. Bencho's licence page (bencho.dev/licence, last updated
12 October 2026) says Pro blocks may be used in anything you make, and "an open source project is
fine, as long as the block is part of the thing it builds rather than offered on its own"; they
may not be passed on as blocks (on their own, or in a UI kit, component library, template,
snippet collection, or a service that hands blocks to others). Every Pro adaptation is in
`web/components/bencho-pro/`, with a README stating that licence, apart from the MIT code.

| Block | Licence | Used for | Where |
|---|---|---|---|
| Text fade (`text-fade`) | Pro | Lead headline and summary on load; newly arrived events | `web/components/bencho-pro/text-fade/` |
| Reorder list (`liq-arrange`) | Pro | Dragging widgets in the rail | `web/components/bencho-pro/arrange/` |
| Notification widget (`notify-widget`) | Pro | The "N new events" bar | `web/components/bencho-pro/new-events-bar.tsx` |
| FAQ accordion (`faq-accordion`) | Pro | Technical details expand | `web/components/bencho-pro/technical-details.tsx` |
| Theme switch (`theme-switch`) | Pro | Header theme switch | `web/components/bencho-pro/theme-switch.tsx` |
| Image shimmer (`image-shimmer`) | Pro | The reserved picture box while a picture loads, kept monochrome (its colour prism dropped) | `web/components/bencho-pro/image-shimmer.css` |
| Skeleton morph (`skeleton-morph`) | Pro | Loading skeleton bars that breathe in colour, in the final layout's boxes | `web/components/bencho-pro/home-skeleton.tsx` |
| Stacked bars (`stacked-bars`) | MIT | The exploitation chart's ring, step-back and gliding tooltip | `web/components/widgets/exploitation-chart.tsx` (notice in `web/licenses/bencho-mit.txt`) |
| Search (`seek`), Rolling counter (`rolling-counter`) | MIT | Header search; the count in the new-events bar | unchanged from the first round |

How Text fade's tokens map: `--ink` and `--fill-on` inherit the surrounding text colour (headline
ink, summary ink-2), `--signal` is our focus colour, `--d` and `--trv-dur` are set inline per word.
Its press-to-replay behaviour is removed because the text is a link.

### shadcn/ui components used

Added in the image-led round: `aspect-ratio` (every picture and tile, reserving its box),
`card` (each widget), `toggle-group` (the chart's view switcher, present in the component but not
rendered while only one view exists). The tab underline uses Base UI's `Tabs.Indicator` under the
shadcn `tabs`, and the loading skeleton is built from `skeleton`.
Still used: `item` (feed rows), `tabs` (section tabs), `collapsible` (Technical details), `badge`
(trust label), `separator`, `empty`, `skeleton`, `input`, `button`.

### Contrast (WCAG 2), measured

Measured with `node web/scripts/contrast.mjs` from the tokens in `web/app/globals.css`, including
the colours computed by `color-mix()`. Every pair passes AA (4.5:1 for text, 3:1 for non-text
marks).

| Pair | Use | Light | Dark | Needs |
|---|---|---|---|---|
| `c-ink` on `c-bg` | Headlines, organisation, body | 18.88:1 | 15.85:1 | 4.5:1 |
| `c-ink-2` on `c-bg` | Summaries, excerpts | 11.40:1 | 10.51:1 | 4.5:1 |
| `c-ink-3` on `c-bg` | Metadata, timestamps, tabs | 6.27:1 | 6.48:1 | 4.5:1 |
| `c-ink-3` on `c-surface` | Metadata on surfaces | 5.85:1 | 5.97:1 | 4.5:1 |
| `c-accent` on `c-bg` | LIVE kicker, attacker-claim label | 6.29:1 | 5.82:1 | 4.5:1 |
| `c-accent` on `c-accent-soft` | Sample data banner label | 5.56:1 | 5.08:1 | 4.5:1 |
| `c-ink` on `c-accent-soft` | Sample data banner text | 16.67:1 | 13.83:1 | 4.5:1 |
| `c-bg` on `c-ink` | New-events bar text | 18.88:1 | 15.85:1 | 4.5:1 |
| `c-rule-strong` on `c-bg` | Section rules (non-text) | 18.88:1 | 15.85:1 | 3:1 |
| `c-ink` on `c-surface` | Widget titles and values | 17.60:1 | 14.62:1 | 4.5:1 |
| `c-ink-2` on `c-surface` | Chart labels, widget text | 10.63:1 | 9.69:1 | 4.5:1 |
| `c-accent` on `c-surface` | Spike columns (non-text) | 5.87:1 | 5.37:1 | 3:1 |
| `chart-grey` on `c-surface` | Other chart columns (non-text) | 3.26:1 | 3.18:1 | 3:1 |
| `#f6f5f1` on 75% `#111111` over white | Image credit on the lightest possible picture | 7.75:1 | 7.75:1 | 4.5:1 |
| `c-ink` on `tile-1`…`tile-5` | Tile logo or lettermark | 16.26–16.64:1 | 13.78–14.01:1 | 3:1 |
| `c-ink-2` on `tile-1`…`tile-5` | Tile organisation caption | 9.81–10.04:1 | 9.14–9.29:1 | 4.5:1 |

Light tokens now: ground `#ffffff`, surface `#f7f7f5`, ink `#111111` / `#3a3a38` / `#62605c`,
rule `#e4e2dd`, muted red `#b0322b` on `#fbeeec`, tile grounds `#f2f0eb` `#edf0eb` `#eceef2`
`#f5f0e7` `#f4ede9`. Dark is unchanged.

The chart's two mark colours were also run through the dataviz skill's palette validator against
each theme's widget surface: CVD separation ΔE 13.9 (light) and 9.0 (dark), normal-vision ΔE 20.4
and 19.4, both above 3:1 on the surface. Its "chroma floor" check flags the grey, which is the
intended de-emphasis grey of the emphasis form, not a categorical colour. Spike months also carry
their value above the column, so colour is never the only signal.

## Event page (ticket #11), 2026-11-26

(These images were replaced by the merged set at the top on 2026-11-26.) `event-light.png`,
`event-dark.png` and `event-phone-light.png`: the page for the real 1Password
event, which three outlets reported (BleepingComputer, Security Affairs, The Hacker News). A
production build against a database seeded from every real RSS capture in
`api/tests/fixtures/real` (no live fetch, no AI summaries, so the summary is the earliest
publisher's excerpt), as a reader in London sees it. The picture is The Hacker News's own feed
image, loaded by the browser from the publisher and credited on it. Captured with
`EVENT_PATH=/events/3 ONLY=event LOOKS=light,dark,phone-light node scripts/capture-checkpoint.mjs`.
