# Homepage design checkpoint (ticket #9), image-led revision

Screenshots for the owner's sign-off, taken on 2026-11-26 from a production build, as a reader in
London sees them (times are the reader's local time). This revision follows Niko's review of the
first, text-only design (see "Niko's review of the first homepage design" in
`docs/wiki/design-direction.md`).

The real feed shows what one worker run stored from the live feeds on that date: 131 events, 13 of
them on the All tab, 79 source records with a publisher image. The Hacker News and Google Threat
Intelligence refused the connection on that run and were not retried. The sample-data preview
(`/preview`) shows the same components with every field and widget that later tickets fill. Its
events and figures are invented, and a banner on every screen says so.

| | Light | Dark | Phone light | Phone dark | Tablet light | Tablet dark |
|---|---|---|---|---|---|---|
| Real feed (`/`) | [feed-light](feed-light.png) | [feed-dark](feed-dark.png) | [feed-phone-light](feed-phone-light.png) | [feed-phone-dark](feed-phone-dark.png) | [feed-tablet-light](feed-tablet-light.png) | [feed-tablet-dark](feed-tablet-dark.png) |
| Sample data (`/preview`) | [sample-preview-light](sample-preview-light.png) | [sample-preview-dark](sample-preview-dark.png) | [sample-preview-phone-light](sample-preview-phone-light.png) | [sample-preview-phone-dark](sample-preview-phone-dark.png) | [sample-preview-tablet-light](sample-preview-tablet-light.png) | [sample-preview-tablet-dark](sample-preview-tablet-dark.png) |

Desktop is 1440px wide, phone 390px (at 2x), tablet 820px. In each image the first feed row's
"Technical details" is open. To regenerate: run a web build with `SAMPLE_PREVIEW=1` against an API
with real events, then `BASE_URL=http://127.0.0.1:3000 node web/scripts/capture-checkpoint.mjs`.

## What changed against the owner's review

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
| Stacked bars (`stacked-bars`) | MIT | The exploitation chart's ring, step-back and gliding tooltip | `web/components/widgets/exploitation-chart.tsx` (notice in `web/licenses/bencho-mit.txt`) |
| Search (`seek`), Rolling counter (`rolling-counter`) | MIT | Header search; the count in the new-events bar | unchanged from the first round |

How Text fade's tokens map: `--ink` and `--fill-on` inherit the surrounding text colour (headline
ink, summary ink-2), `--signal` is our focus colour, `--d` and `--trv-dur` are set inline per word.
Its press-to-replay behaviour is removed because the text is a link.

## shadcn/ui components used

New this round: `aspect-ratio` (every picture and tile), `card` (each widget), `toggle-group` (the
chart's view switcher, present in the component but not rendered while only one view exists).
Still used: `item` (feed rows), `tabs` (section tabs), `collapsible` (Technical details), `badge`
(trust label), `separator`, `empty`, `skeleton`, `input`, `button`.

## Contrast (WCAG 2), measured

Measured with `node web/scripts/contrast.mjs` from the tokens in `web/app/globals.css`, including
the colours computed by `color-mix()`. Every pair passes AA (4.5:1 for text, 3:1 for non-text
marks).

| Pair | Use | Light | Dark | Needs |
|---|---|---|---|---|
| `c-ink` on `c-bg` | Headlines, organisation, body | 17.31:1 | 15.85:1 | 4.5:1 |
| `c-ink-2` on `c-bg` | Summaries, excerpts | 10.45:1 | 10.51:1 | 4.5:1 |
| `c-ink-3` on `c-bg` | Metadata, timestamps, tabs | 5.58:1 | 6.48:1 | 4.5:1 |
| `c-ink-3` on `c-surface` | Metadata on surfaces | 5.83:1 | 5.97:1 | 4.5:1 |
| `c-accent` on `c-bg` | LIVE kicker, attacker-claim label | 6.31:1 | 5.82:1 | 4.5:1 |
| `c-accent` on `c-accent-soft` | Sample data banner label | 5.56:1 | 5.08:1 | 4.5:1 |
| `c-ink` on `c-accent-soft` | Sample data banner text | 15.26:1 | 13.83:1 | 4.5:1 |
| `c-bg` on `c-ink` | New-events bar text | 17.31:1 | 15.85:1 | 4.5:1 |
| `c-rule-strong` on `c-bg` | Section rules (non-text) | 17.31:1 | 15.85:1 | 3:1 |
| `c-ink` on `c-surface` | Widget titles and values | 18.09:1 | 14.62:1 | 4.5:1 |
| `c-ink-2` on `c-surface` | Chart labels, widget text | 10.92:1 | 9.69:1 | 4.5:1 |
| `c-accent` on `c-surface` | Spike columns (non-text) | 6.60:1 | 5.37:1 | 3:1 |
| `chart-grey` on `c-surface` | Other chart columns (non-text) | 3.30:1 | 3.18:1 | 3:1 |
| `#f6f5f1` on 75% `#111111` over white | Image credit on the lightest possible picture | 7.75:1 | 7.75:1 | 4.5:1 |
| `c-ink` on `tile-1`…`tile-5` | Tile logo or lettermark | 14.84–15.42:1 | 13.78–14.01:1 | 3:1 |
| `c-ink-2` on `tile-1`…`tile-5` | Tile organisation caption | 8.96–9.31:1 | 9.14–9.29:1 | 4.5:1 |

The chart's two mark colours were also run through the dataviz skill's palette validator against
each theme's widget surface: CVD separation ΔE 15.7 (light) and 9.0 (dark), normal-vision ΔE 21.0
and 19.4, both above 3:1 on the surface. Its "chroma floor" check flags the grey, which is the
intended de-emphasis grey of the emphasis form, not a categorical colour. Spike months also carry
their value above the column, so colour is never the only signal.
