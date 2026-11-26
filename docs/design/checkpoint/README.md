# Homepage design checkpoint (ticket #9)

Screenshots for the owner's sign-off, taken on 2026-11-26 from a production build. The real feed
shows the 15 events one worker run stored from BleepingComputer's live feed on that date. The
sample-data preview (`/preview`) shows the same components with every field that later tickets
fill. Its events are invented, and a banner on every screen says so.

| | Light | Dark | Phone light | Phone dark | Tablet |
|---|---|---|---|---|---|
| Real feed (`/`) | [feed-light](feed-light.png) | [feed-dark](feed-dark.png) | [feed-phone-light](feed-phone-light.png) | [feed-phone-dark](feed-phone-dark.png) | [feed-tablet-light](feed-tablet-light.png) |
| Sample data (`/preview`) | [sample-preview-light](sample-preview-light.png) | [sample-preview-dark](sample-preview-dark.png) | [sample-preview-phone-light](sample-preview-phone-light.png) | [sample-preview-phone-dark](sample-preview-phone-dark.png) | [sample-preview-tablet-light](sample-preview-tablet-light.png) |

Desktop is 1280px wide, phone 390px (at 2x), tablet 820px. In each image the second row's
"Technical details" is open. To regenerate, run a web build with `SAMPLE_PREVIEW=1` against an
API with real events, then `BASE_URL=http://127.0.0.1:3000 node web/scripts/capture-checkpoint.mjs`.

## What the real feed shows today

The API currently returns only the headline, link, publisher, times and the publisher's excerpt.
Fields that later tickets fill show a quiet empty state on the real feed and are never guessed:

| Field | Filled by | Empty state on the real feed |
|---|---|---|
| Affected organisation | entity extraction | kicker line omitted |
| Plain-language summary (labelled "AI summary") | enrichment | the publisher's own excerpt, unlabelled, two lines |
| Category | classifier (#6) | kicker omitted; "Not classified yet" in details |
| Trust label and score | verifier and scorer | "Not yet assessed", with no score |
| Additional sources | deduplicator (#5) | "+N sources" omitted |
| CVE identifiers, attack vector | normaliser, enrichment | "Not extracted yet", "Not identified yet" in details |
| Action line | enrichment | omitted |
| Live status in the header | source health (#3) | "Source status not reported yet" |
| Section tabs other than All | classifier (#6) | "Nothing filed under X yet", explaining that every event is under All for now |

## Wordmark

Built option 3 from the design notes: **Compromised** in Helvetica Neue Bold, title case, with
"KNOW WHAT'S BEEN COMPROMISED" beneath in small tracked capitals, both on one left edge. Why:
title case reads as the name of a publication, as the FT's and Reuters' do, rather than a
startup logo. The tagline tells a first-time, non-technical reader what the site is. And it
leaves the muted red for meaning (live events, attacker claims) instead of decoration, which
option 1's red full stop would not.

## Mobbin references used

From the design research notes, plus one new search for the phone header and tabs:

| Where | Reference |
|---|---|
| Row structure: time gutter, kicker, headline, summary, hairlines between rows | NYT Latest, https://mobbin.com/screens/28844f36-ab35-441e-a93b-cb48af285b8e |
| Red used only for the LIVE kicker; heavy rule under the section nav | NYT homepage, https://mobbin.com/screens/cb3938b3-d8af-4c12-a997-a7ecb83662f2 |
| Row density: bold title over one muted metadata line | Matter, https://mobbin.com/screens/cae30201-5eac-4644-b476-19a5df22c410 |
| Monospace times and identifiers | T1 Energy, https://mobbin.com/sites/sections/b9b87253-7e2f-480b-ae31-74bd0b240aa5 |
| Day separators on a full-width rule | Basecamp, https://mobbin.com/screens/3119c9f0-832e-448d-b750-03e5a806e9f6 |
| "+N sources" count | Perplexity Discover, https://mobbin.com/screens/ec59e633-ba10-46a5-9277-363061007f02 and https://mobbin.com/screens/59c4edb3-02b7-4642-9388-1e2c392eba36 (new search) |
| Plain-words reliability label with a caution line (attacker claims) | Fey, https://mobbin.com/screens/5843d906-38f9-4c8c-8dba-cbeb8ce4453f |
| Underline tabs under the search field, sideways scroll on phones | Substack search, https://mobbin.com/screens/bb39052c-33ec-48e9-add4-c57a0230dd54; X Explore, https://mobbin.com/screens/6bf7d0b1-2e65-4b83-b8df-fb05051c62d1 (new search) |
| Phone row: time and source line over the headline | Perplexity iOS, https://mobbin.com/screens/071f652d-f323-4b96-a14c-e405e92eebc6 |
| Quiet theme control, dark editorial rules | Quartz, https://mobbin.com/screens/3d7f16c7-6f6a-41a8-8ee5-1edfbc54ca98 |

## Bencho blocks used

All five were fetched with the Bencho MCP's `get_block` without errors, then restyled.

| Block | Licence | Used for | Kept | Removed or changed |
|---|---|---|---|---|
| `notify-widget` | Pro | "N new events" bar (`web/components/feed/new-events-bar.tsx`) | The pill and its AnimatePresence `popLayout` text swap (framer-motion) | Dropdown card, avatars package, bell shake; restyled as a full-width ink bar with square corners |
| `faq-accordion` | Pro | "Technical details" expand (`web/components/feed/technical-details.tsx`) | The `grid-template-rows: 0fr → 1fr` opening and the chevron that flips | Word-by-word blur reveal (decorative). Open/closed state comes from the shadcn Collapsible |
| `theme-switch` | Pro | Header theme switch (`web/components/site/theme-switch.tsx`) | Both icons always visible, a disc that slides between them, reading the page's own theme from the root element | Resized to 64x32 with a hairline border; frame painting removed; driven by next-themes |
| `seek` | MIT | Header search on tablet and desktop (`web/components/site/search-field.tsx`) | One object whose width is the state, the lens fixed at its inset, press feedback, Escape and empty-blur to close | Corner 2, no cursor magnet, no glass; a CSS overshoot curve instead of its JS spring; the field is the shadcn Input |
| `rolling-counter` | MIT | The count in the new-events bar (`web/components/feed/rolling-number.tsx`) | Digit strips behind a masked window, monospace tabular digits | Buttons, drag and fling; a CSS transition instead of its per-column spring |

Pro blocks may be used in anything built but not redistributed as blocks. These are adapted into
the site's own components, not shipped as Bencho blocks. The `gauge` block was not used, as the
notes recommend: a dial invites reading the score as a measurement.

## shadcn/ui components used

`item` (each feed row), `tabs` (section tabs, line variant, each tab a link), `collapsible`
(Technical details), `badge` (trust label), `separator` (row rules), `empty` (empty sections),
`skeleton` (loading state), `input` (search field), `button` (already present). Theming is
next-themes, as shadcn's dark-mode guide prescribes. shadcn's colour variables are mapped onto
the Compromised tokens in `web/app/globals.css`, so every primitive follows the palette.

## Contrast (WCAG 2), measured

Measured with `node web/scripts/contrast.mjs` from the tokens in `web/app/globals.css`:

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
| `c-rule-strong` on `c-bg` | Section and day rules (non-text) | 17.31:1 | 15.85:1 | 3:1 |

Changes from the proposed tokens:
- Dark accent `#D2625B` became `#D9706A`. On the dark accent-soft tint it measured 4.42:1, below AA.
- `ink-3` was darkened in light (`#6A6864` to `#64625E`, 5.10 to 5.58:1) and lightened in dark
  (`#8F8C86` to `#9A9790`, 5.63 to 6.48:1). It carries 11-12px text, so it needs margin above the minimum.
- The dark surface and rule (`#1A1A19`, `#2E2D2B`) were nudged so hairlines stay visible.
