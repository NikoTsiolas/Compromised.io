# Social-feed options for the homepage (design exploration, 2026-11-26)

**Sample content.** Every company, event, publisher and figure in these images is invented
(Microsoft's sample names: Fabrikam, Northwind, Tailspin, Woodgrove, Adatum, Litware). Photos are
grey placeholders. Nothing here is a real incident.

Niko's review of the image-led page (commit 4ed58c7): "this is a bit too news esque. needs to be more
of a feed like a social media feed I think. I think that's easier to digest." He asked for a few
designs in Figma. These are three, for him to compare. No app code was changed.

Figma file: https://www.figma.com/design/plOOtLTSKg9RuAphEHP3CM (Niko's "Funktion" team, Pro plan,
in his drafts). Pages: Overview, Option A, Option B, Option C, Foundations.

| | Phone light | Phone dark | Desktop 1440 |
|---|---|---|---|
| Overview (three phones side by side, recommendation) | [overview](overview.png) | | |
| A · Timeline | [option-a-phone-light](option-a-phone-light.png) | [option-a-phone-dark](option-a-phone-dark.png) | [option-a-desktop](option-a-desktop.png) |
| B · Big cards | [option-b-phone-light](option-b-phone-light.png) | [option-b-phone-dark](option-b-phone-dark.png) | [option-b-desktop](option-b-desktop.png) |
| C · Three columns | [option-c-phone-light](option-c-phone-light.png) (and [charts tab](option-c-phone-charts-tab.png)) | [option-c-phone-dark](option-c-phone-dark.png) | [option-c-desktop](option-c-desktop.png) |

Exported at 1x from Figma.

## The options

**A · Timeline** (like Threads or X). One narrow column. Each event is a post from the affected
company: its logo or lettermark as the avatar, company, category and time on one line, the original
headline (linking to the publisher), the AI summary, Advice from source when there is one, an
optional photo, the trust label with score and sources, and a quiet action row (outlet count,
Details, Share, Watch). Desktop: the column beside the widget rail. Phone: the widgets drop into
the feed as cards between posts; a floating "3 new events" pill.

**B · Big cards** (like Instagram or Artifact). One story per card: company on top, a full-width
photo or a large lettermark tile, an action row, then headline, AI summary and trust label.
Category chips instead of underline tabs. Desktop: two columns of cards beside the rail. Phone:
edge-to-edge cards; the four widgets are a sideways carousel after the second card.

**C · Three columns** (X's desktop shell with Reddit-style cards). Left navigation with the seven
categories and a "Watching" list kept in the browser; bordered post cards in the middle, each
ending in a trust strip with a score bar (pale red for attacker claims); widgets on the right.
Phone: cards on a grey ground, "Watch" in the card header (where Reddit puts "Join"), and a bottom
tab bar (Feed, Search, Watching, Charts) with the widgets behind Charts.

All three keep the settled parts: plain language, verbatim headline, labelled AI summary, Advice
from source only when present, trust label + 0-100 score + source names together, red only for
live and attacker claims, struck-through "Disputed", technical details expand (shown open on the
Fabrikam post), the tabs, search, theme toggle, wordmark and tagline, live status, the four
widgets, white ground by default and a dark variant. No like, reply, repost, follower or view
counts anywhere.

## Recommendation: A

- Most like a social feed and least like a news page.
- Works with or without a photo. On 26 Nov only 6 of 11 real events had a publisher photo; in A a
  photo is an attachment, in B half the cards would be big letter tiles.
- One layout on phone and desktop, mostly a rearrangement of components the app already has.
- B puts publisher photos at full size, and some publishers use the banned imagery (Dark Reading's
  hooded figure on 26 Nov).
- Worth borrowing from C later: the Watching list and the phone bottom tab bar.

## References

Mobbin (searched with the Mobbin MCP, `search_screens`, on 2026-11-26):

| Option | Screen |
|---|---|
| A | Threads home feed: https://mobbin.com/screens/fe72d204-7d68-47a3-bbf2-ca5aafe2969c |
| A | Threads post with photo: https://mobbin.com/screens/f5368d67-a447-4f4a-bddd-3e321815f3cb |
| A | Threads post, like count hidden: https://mobbin.com/screens/f232fd1a-2153-48fe-9567-933ce19de8a4 |
| A | X web timeline with media and right rail: https://mobbin.com/screens/e3175c87-df8d-4c17-a24a-5f6157e44154 |
| A, C | Bluesky feed with interleaved card and bottom tab bar: https://mobbin.com/screens/fbf2ae20-3add-4b69-815f-a5a7a15a1a9b |
| B | Instagram home feed: https://mobbin.com/screens/f95624c3-820d-4009-bb0b-59a53f3ba585 |
| B | Instagram "Suggested reels" carousel: https://mobbin.com/screens/f5ce72ad-1ae5-47d3-abde-989324593482 |
| B | Artifact big story cards: https://mobbin.com/screens/f29a1387-48fc-4b42-9770-8e6edeadb018 |
| B | Artifact list with publisher logo and time: https://mobbin.com/screens/f452b3d0-4ee6-4d26-996e-26bf611a7613 |
| C | X web three-column layout: https://mobbin.com/screens/fc04d864-4483-460a-bc35-0cdc61af6c89 |
| C | Reddit web cards with pill actions: https://mobbin.com/screens/fdde04df-52c8-40fb-bbf3-c1f04f5661f1 |
| C | Reddit web left navigation: https://mobbin.com/screens/fd41c55a-317e-46b3-a989-39edf3a0e088 |
| C | Reddit community feed, "Join" in header: https://mobbin.com/screens/feaeb88e-00f8-4472-8c41-f5da2b07abfa |

Bencho blocks (Bencho MCP `search_blocks`; `get_block` read for `tab-bar` (Pro) and `pull` (MIT)):

| Option | Blocks |
|---|---|
| A | notify-widget (new-events pill, already in app), pull (pull to refresh, MIT), faq-accordion (details, already in app), text-fade (new posts), glide-tip (action tooltips), load-cards (skeletons) |
| B | expand-card (card opens into details), jelly-tabs (category chips), image-shimmer (photo loading, already in app), load-cards, notify-widget, liq-arrange (rail) |
| C | tab-bar (phone bottom navigation, Pro), liq-arrange (widget reorder), stacked-bars (chart, MIT, already in app), notify-widget, faq-accordion, theme-switch |

Licences of blocks other than `tab-bar` and `pull` were not re-read in this round.

## Figma structure

- Variables: collection "Compromised tokens" with Light and Dark modes, values copied from
  `web/app/globals.css` (bg, surface, ink 1-3, rule, accent, accent-soft, tile 1-5, chart grey,
  photo placeholder greys). Dark frames are the light frames with the Dark mode applied.
- Text styles `Sans/*` and `Mono/*`. **Roboto and Roboto Mono stand in** for Helvetica Neue and
  the system monospace: the Figma MCP runs on Figma's servers and cannot load Helvetica Neue or
  Arial. Changing the family on the text styles restores Helvetica Neue in one step.
- Components on the Foundations page: Trust (variants Confirmed, Reported, Claimed, Disputed with
  Label, Score and Sources text properties), Avatar, Action (Quiet, Pill), Photo placeholder,
  Technical details, the four widgets, Sample banner, Wordmark, Live status, Theme toggle, Search
  field, New events pill, Tabs (underline and chips), icons (Lucide). Option C's page holds the
  bottom tab bar component.
