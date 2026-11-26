# Homepage design checkpoint (ticket #9), white and smooth revision

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

| | Light | Dark | Phone light | Phone dark | Tablet light | Tablet dark |
|---|---|---|---|---|---|---|
| Real feed (`/`) | [feed-light](feed-light.png) | [feed-dark](feed-dark.png) | [feed-phone-light](feed-phone-light.png) | [feed-phone-dark](feed-phone-dark.png) | [feed-tablet-light](feed-tablet-light.png) | [feed-tablet-dark](feed-tablet-dark.png) |
| Sample data (`/preview`) | [sample-preview-light](sample-preview-light.png) | [sample-preview-dark](sample-preview-dark.png) | [sample-preview-phone-light](sample-preview-phone-light.png) | [sample-preview-phone-dark](sample-preview-phone-dark.png) | [sample-preview-tablet-light](sample-preview-tablet-light.png) | [sample-preview-tablet-dark](sample-preview-tablet-dark.png) |

Desktop is 1440px wide, phone 390px (at 2x), tablet 820px. In each image the first feed row's
"Technical details" is open. To regenerate: run a web build with `SAMPLE_PREVIEW=1` against an API
with real events, then `BASE_URL=http://127.0.0.1:3000 node web/scripts/capture-checkpoint.mjs`.

## What changed in the second review

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

## What changed against the owner's first review

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

## What the real feed shows today

Widgets other than source status have no API yet (issue #15). On the real page they say so
quietly ("No figures yet", "Nothing listed yet") and show no invented values. Fields later tickets
fill keep their quiet empty states: "Not yet assessed" instead of a trust label and score, the
publisher's own excerpt (unlabelled) instead of an AI summary, "+N sources" omitted until
grouping (#5).

Note for the owner: a publisher's picture is the publisher's choice. Some use exactly the imagery
the brief bans (on this date Dark Reading's picture for the .NET story is a hooded figure in front
of green code). The switch above turns all publisher pictures off if that is not acceptable.

## Mobbin references used

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

## Bencho blocks used

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

## shadcn/ui components used

Added in the image-led round: `aspect-ratio` (every picture and tile, reserving its box),
`card` (each widget), `toggle-group` (the chart's view switcher, present in the component but not
rendered while only one view exists). The tab underline uses Base UI's `Tabs.Indicator` under the
shadcn `tabs`, and the loading skeleton is built from `skeleton`.
Still used: `item` (feed rows), `tabs` (section tabs), `collapsible` (Technical details), `badge`
(trust label), `separator`, `empty`, `skeleton`, `input`, `button`.

## Contrast (WCAG 2), measured

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
