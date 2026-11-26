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
files below; nothing outside this folder contains Pro block code.

| File | Bencho block | What was kept / changed |
|---|---|---|
| `text-fade/text-fade.tsx`, `text-fade/text-fade.css` | Text fade (`text-fade`, TextReveal) | The blur-rise keyframe, expo-out easing and one-keyframe-many-delays method, with the block's comments. Words split only; press-to-replay removed; tokens mapped to ours. |
| `text-fade/arrival-fade.tsx` | Text fade (as above) | Plays the fade only for events that arrive after the page loaded. |
| `arrange/widget-rail.tsx`, `arrange/arrangement.ts` | Reorder list (`liq-arrange`, Arrange) | Pointer drag pinned to its start slot, reorder under the gesture, elastic spring. Goo filter, squash and lean removed; handle, keyboard moves and side switch added. |
| `new-events-bar.tsx` | Notification widget (`notify-widget`) | The pill and its rolling "N new" swap only. |
| `theme-switch.tsx` | Theme switch (`theme-switch`) | Restyled; driven by next-themes. |

MIT-licensed Bencho blocks (for example Stacked bars, used by the exploitation chart) stay with
the code that uses them and carry their copyright notice there.
