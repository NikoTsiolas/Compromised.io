# Design direction

- 2026-11-26: From the brief: near-black and off-white palette, muted red as a restrained accent, thin dividers, compact readable rows, light and dark themes, responsive, minimal functional animation, a typographic wordmark. No neon green, Matrix imagery, hooded figures, shields, heavy gradients or threat maps.
- 2026-11-26: With the audience change, Niko chose the Financial Times / Reuters editorial feel and dropped Bloomberg Terminal density.
- 2026-11-26: Claude proposed Newsreader, Inter and JetBrains Mono. Niko rejected anything that reads as "AI-esque" and chose Helvetica Neue, in an International (Swiss) style.
- 2026-11-26: Helvetica Neue is licensed, so it is named as a system font: Apple devices render it, others fall back to Arial or Roboto. No font files are shipped. Niko accepted this.
- 2026-11-26: Assumed, not confirmed: timestamps and CVE numbers in a monospace face (that part of Niko's dictated answer was garbled).
- 2026-11-26: Components and references must come from shadcn, the Mobbin MCP and the Bencho MCP. Niko repeated this three times.
- 2026-11-26: Niko mentioned an "Impeccable" library he uses. Nothing by that name was installed on the machine; unresolved.
- 2026-11-26: Design checkpoint: the homepage feed is built first with real ingested data, and Niko signs off the look before other pages are built.

## Reference gathering on 2026-11-26
A subagent used all three required tools and wrote `design-references.md` in the research notes folder (see [Working agreements](working-agreements.md)).
- 2026-11-26: Mobbin: 20 references kept from 15 searches. Closest matches: NYT's Latest list and filter flow, Matter's compact rows, T1 Energy's monospace dates, Perplexity's source count and source panel, Fey's "Consider with caution" label, and Hashnode, Better Stack and SCMP for timelines. Mobbin returned no FT or Reuters screens and nothing like a "N new events" bar.
- 2026-11-26: Bencho: 6 blocks recorded (notify-widget, faq-accordion, theme-switch, seek, rolling-counter, gauge; the gauge was recommended against). Three need a Bencho Pro licence; whether Niko holds one was unknown.
- 2026-11-26: shadcn: 19 components listed with Tailwind v4 and next-themes setup. Its docs disagreed on whether Toast is deprecated in favour of Sonner.
- 2026-11-26: Proposed direction, not yet seen by Niko: text-only rows divided by thin lines, a monospace time column on the left, company name and plain-language summary first; #111111 on #F6F5F1, reversed in dark mode; muted red #A3322C only for live items and attacker claims; trust label and score as one component that distinguishes statuses by square markers, not colour. Colour contrast had not been measured.

## Homepage design built for sign-off, 2026-11-26
As of `NikoTsiolas/Compromised.io@bd56fbb` on branch `ticket-9-homepage-design` (ticket #9, built by an Opus subagent, CI green, not merged pending Niko's sign-off):
- Wordmark: "Compromised" in title case with the tagline beneath.
- The proposed dark-theme accent failed contrast on its tint (4.42:1) and was changed to #D9706A (5.08:1); all text and accent pairs then passed WCAG AA in both themes.
- Bencho blocks used: notify-widget, faq-accordion, theme-switch (Pro), seek and rolling-counter (MIT); gauge skipped. shadcn: item, tabs, collapsible, badge, separator, empty, skeleton, input, button.
- Screenshots and the reference list were in `docs/design/checkpoint/` on that branch. A `/preview` route showed the populated design under a "Sample data" banner and was excluded from production builds.
- Gaps reported: the search control pointed at `/search`, which did not exist yet; the new-events count came from a Next route handler because the API had no count endpoint; times were shown in UTC; tablet was captured in light only and had no test.

## Niko's review of the first homepage design, 2026-11-26
- Niko did not approve the text-only design at `bd56fbb`. He asked for a more image-led page modelled on Perplexity's Discover screen (he pasted a Mobbin capture of it): a featured section with a large lead image and a row of image cards, then the feed below with images.
- He asked for widgets beside the feed, built from Bencho blocks, that the reader can move around, and for a chart of exploitation over the months with the months where attacks spiked highlighted. He later added two more chart views: increase in frequency, and "different depts", which Claude read as sectors (healthcare, finance, government and so on) and as "availability" incidents that take a service offline. Niko had not confirmed that reading on this date.
- He pasted Bencho's "Text fade" block (Pro licence) as "the vibe" he wants for how text appears: words easing in from a soft blur.
- Images: only 5 of the 14 feeds carried an image in the feed itself (Dark Reading, The Hacker News, The Record, Unit 42, Cisco Talos). Claude asked twice whether to use them; Niko did not answer. Claude proceeded on its recommendation: show the image a publisher puts in its own feed, loaded directly from the publisher with credit and never copied to the server, behind a configuration switch; every other event gets a designed tile with the company's logo or lettermark. This narrows the 2026-11-26 "headline, link and excerpt only" storage decision by adding one image URL per source record. Scraping article pages for images stays ruled out, and Ransomware.live's images (screenshots of leak sites) are never used.
- Defaults Claude stated and Niko did not object to: the featured story is picked by rule (most independent sources in 24 hours, confirmed or credibly reported, never an attacker claim); the frequency chart draws on CISA's exploited-vulnerabilities history; the sidebar ticket (#13) is absorbed into the design ticket (#9).
- Unresolved on this date: Bencho's Pro licence says a Pro block may be used in anything you build but not redistributed. The repository is intended to be public, and the design uses Pro blocks. Whether a public repository counts as redistribution had not been checked.

## Niko's review of the image-led redesign, 2026-11-26
As of `NikoTsiolas/Compromised.io@a4461c4` on branch `claude/ticket-9-homepage-redesign-c56e9b` (CI green, not merged):
- The layout followed the Perplexity Discover reference, but on the real feed only two rows showed a photo; the rest were letter tiles. Causes: five sources carry feed images, The Record serves its images over http, and 162 of 351 catalog logo keys did not resolve in Simple Icons (Microsoft, Adobe, Amazon, Chrome among them).
- Niko approved fetching each article's preview image address from the publisher's own site ("yea fetch them"). This reverses Claude's earlier rule against fetching article pages, in a narrowed form: only pages on a host the source's registry entry declares as the publisher's own, only the og:image address is read, and the image itself is still loaded by the reader's browser from the publisher.
- Niko asked for a white site ("not a fan of the black") and for everything to be "very smooth". Claude's reading: pure white ground, light as the default for everyone, dark kept behind the toggle; smooth motion across every interaction with reduced motion honoured. Niko had not confirmed whether the dark theme should be removed entirely.
- Bencho's licence page (updated 2026-10-12, read by the redesign session) said Pro blocks are allowed in an open-source project "as long as the block is part of the thing it builds rather than offered on its own". This resolves the earlier open question: the public repository is allowed. Pro-derived code was kept in `web/components/bencho-pro/`.

## Third design pass, 2026-11-26
As of `NikoTsiolas/Compromised.io@4ed58c7` on branch `claude/ticket-9-homepage-redesign-c56e9b` (CI green, not merged on this date):
- Article preview images: only for records with no feed image, only on hosts declared per source in a new `article_hosts` registry field, one attempt ever, document head only (256 KB), robots.txt honoured, og:image then twitter:image, https only. Stored in an `article_previews` table because records are immutable. CISA, MSRC and Ransomware.live were never fetched.
- On the real feed's All tab 6 of 11 rows showed a photo. SecurityWeek's article pages all failed to fetch (cause unconfirmed) and Krebs's pages carried no preview tag.
- Off-brand images seen: Dark Reading's hooded-figure stock photo; BleepingComputer's red "digital code" illustration. Per-source and global switches existed (`PUBLISHER_IMAGES_OFF_FOR`, `PUBLISHER_IMAGES`).
- Light ground pure white, light the default for every visitor, dark behind the toggle; muted red became #b0322b; all pairs passed WCAG AA.
- Motion from three durations (140, 220, 320 ms) and one easing curve; measured layout shift 0.0005 to 0.0026 on desktop and 0 on phone.
- Content security policy used `'unsafe-inline'` for scripts and styles because Next could not use nonces with partial prerendering; `img-src` allowed any https host.
- In that session's capture four sources showed as failing: The Hacker News, Google Threat Intelligence, CISA advisories (403) and MSRC (400). The merge subagent had recorded a 200 from CISA advisories earlier the same day with the new user agent. Unreconciled on this date.
- The redesign's `trustLabel()` mapped "confirmed" to "Confirmed by the company", which ticket #7 showed would be false for CISA and vendor research posts; it needed to display the API's `trust.label` instead.
