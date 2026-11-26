# Bencho Pro blocks

Everything in this folder is adapted from blocks in [Bencho](https://bencho.dev) that are under
the **Bencho Pro licence**, not under this repository's MIT licence. It is kept apart from the
MIT code so it can be found, audited or replaced in one place.

What the licence says (bencho.dev/licence, last updated 12 October 2026, read 26 November 2026):
Pro blocks may be used, copied and changed in any number of things you make, and "an open
source project is fine, as long as the block is part of the thing it builds rather than offered
on its own". They may not be passed on as themselves: not sold, shared, sublicensed or published
on their own, or as part of a UI kit, component library, template, theme, starter or snippet
collection, nor used to build a library or service that hands blocks to other people, nor put
into a model-training dataset. The licence is granted to the person whose account holds Pro (the
project owner). Contributors who take new Pro blocks need their own Pro licence.

So: use these files as part of Compromised. Do not copy them out of this project into another
one, publish them as components, or relicense them under MIT. To drop Bencho Pro, replace the
files below; nothing outside this folder contains Pro block code, apart from two small CSS rules
in `app/globals.css` that this table names.

| File | Bencho block | What was kept / changed |
|---|---|---|
| `text-fade/text-fade.tsx`, `text-fade/text-fade.css` | Text fade (`text-fade`, TextReveal) | The blur-rise keyframe, expo-out easing and one-keyframe-many-delays method, with the block's comments. Words split only; press-to-replay removed; tokens mapped to ours. |
| `text-fade/arrival-fade.tsx` | Text fade (as above) | Plays the fade only for events that arrive after the page loaded, and opens their rows to their height (`.arrival` in `app/globals.css`). |
| `arrange/widget-rail.tsx`, `arrange/arrangement.ts` | Reorder list (`liq-arrange`, Arrange) | Pointer drag pinned to its start slot, reorder under the gesture, elastic spring. Goo filter, squash and lean removed; handle, keyboard moves and side switch added. |
| `image-shimmer.css` | Image shimmer (`image-shimmer`) | The placeholder band of light while a picture loads; its colour prism and rim dropped. |
| `home-skeleton.tsx` (and `.skm-bar` in `app/globals.css`) | Skeleton morph (`skeleton-morph`) | Bars that breathe in colour, not opacity; the morph into content is not used. |
| `technical-details.tsx` | FAQ accordion (`faq-accordion`) | The `0fr -> 1fr` grid-row opening and the flipping chevron; state from the shadcn Collapsible. |
| `new-events-bar.tsx` | Notification widget (`notify-widget`) | The pill and its rolling "N new" swap only. |
| `theme-switch.tsx` | Theme switch (`theme-switch`) | Restyled; driven by next-themes. |
| `bottom-tab-bar.tsx`, `bottom-tab-bar.css` | Tab bar (`tab-bar`, TabBar) | The Feed's phone and tablet bar (#16). Kept: icons until chosen, the name opening in a 0fr -> 1fr column, one tile chasing the chosen item on a spring (bounce 50), concentric softened corners. Changed: links in a `<nav>` with `aria-current` instead of a tablist, every item named for screen readers, our tokens, fixed above the safe area. |
| `glide-tip.tsx` | Liquid tooltip (`glide-tip`, GlideTip) | The "Link copied" pill over a post's Share button (#16). Kept: one spring for the drop's progress driving height, width and lift; the words revealed inside the pill. Dropped: the goo filter, the row of buttons and the sideways glide, hover. |
| `feed-skeleton.tsx`, `feed-skeleton.css` | Load cards (`load-cards`, LoadCards) | The Feed's loading state (#16): post-shaped skeletons easing in out of a blur, a light running over the bars. Its "develop" into content is not used (the server streams the posts). |

MIT-licensed Bencho blocks (for example Stacked bars, used by the exploitation chart) stay with
the code that uses them and carry their copyright notice there.
