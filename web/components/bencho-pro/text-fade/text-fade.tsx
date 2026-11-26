// Text fade, from the Bencho block "Text fade" (TextReveal). Bencho Pro licence: see
// ../README.md. Adapted for Compromised:
//   - only the Words split is used, with each word's delay set at render time from its index,
//     so the server-rendered HTML animates on first paint with no layout reading and no script;
//   - the press-to-replay behaviour (role="button", tabIndex, the replay key and its handlers)
//     is removed: the text is a headline link or a summary, and pressing it must follow the
//     link, not replay an animation;
//   - the words are not aria-hidden behind an aria-label, because the text sits inside a link
//     whose accessible name must stay the headline itself;
//   - its tokens map onto ours in text-fade.css.
// Used with restraint: the lead headline and summary on load, and newly loaded events.
//
// The block's own notes, kept:
/* ══ Text reveal ══════════════════════════════════════════
   A short paragraph that eases in a word at a time — each one
   rising a few pixels out of a soft blur as it fades up — and
   does it again every time you press the text.

   ── ONE KEYFRAME, MANY DELAYS ───────────────────────────
   Every piece runs the same CSS animation; all that differs is
   when it starts, `--i` times the stagger. Nothing is measured
   and nothing runs on a clock, so a long paragraph costs no more
   than a short one. A press bumps a key, the pieces remount, and
   the animation plays from the top.

   ── LETTERS STAY IN THEIR WORDS ─────────────────────────
   Split by letter, each word is still one unbreakable box
   holding its letters, so the paragraph wraps where it always
   did instead of breaking a word across two lines.

   ── EASED, NOT SPRUNG ───────────────────────────────────
   An expo-out: quick off the mark and a long, quiet landing.
   Text that overshoots its line reads as a glitch. */
import { Fragment, type CSSProperties } from "react";

import "./text-fade.css";

export function TextFade({
  text,
  /** Milliseconds before the first word starts (to follow a headline with its summary). */
  delay = 0,
  /** Milliseconds between words. The block's Words split uses 55. */
  step = 40,
  speed = 1,
}: {
  text: string;
  delay?: number;
  step?: number;
  speed?: number;
}) {
  const k = 1 / Math.max(0.25, speed);
  const words = text.split(" ");
  return (
    <span
      className="trv"
      style={{ ["--trv-dur" as string]: `${Math.round(900 * k)}ms` } as CSSProperties}
    >
      {words.map((w, wi) => (
        <Fragment key={wi}>
          <span className="trv-word">
            <span
              className="trv-bit"
              data-fade-word=""
              style={{ ["--d" as string]: `${Math.round(delay + wi * step * k)}ms` } as CSSProperties}
            >
              {w}
            </span>
          </span>
          {wi < words.length - 1 ? " " : null}
        </Fragment>
      ))}
    </span>
  );
}
