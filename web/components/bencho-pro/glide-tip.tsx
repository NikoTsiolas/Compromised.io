"use client";

// A small pill that grows up out of the button that was pressed and says what just happened
// ("Link copied"), then drains back into it. Adapted from the Bencho "Liquid tooltip" block
// (glide-tip, Bencho Pro licence, see README.md). Kept from the block: one number, the drop's
// progress `o` on a spring, from which the pill's height, width and lift are all read, so it
// cannot arrive in pieces; and the words riding inside the pill's own box, revealed as it
// widens. Dropped: the goo filter (it must never touch text), the four-button row and the
// sideways glide (there is one button), and hover (this answers a press, not a pointer).
// Absolutely placed, so the row around the button never moves. Under reduced motion it simply
// appears and disappears.
import { motion, useReducedMotion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

const TIP_H = 26;
const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp = (v: number) => Math.min(1, Math.max(0, v));

export function GlideTip({ text, open }: { text: string; open: boolean }) {
  const still = useReducedMotion();
  const o = useSpring(0, { stiffness: 190, damping: 19 });
  useEffect(() => {
    if (still) o.jump(open ? 1 : 0);
    else o.set(open ? 1 : 0);
  }, [open, o, still]);

  const t = useTransform(o, (v) => clamp(v));
  const height = useTransform(t, (v) => mix(12, TIP_H, v));
  const scaleX = useTransform(t, (v) => mix(0.35, 1, v));
  const y = useTransform(t, (v) => mix(10, 0, v));
  const opacity = useTransform(t, (v) => clamp(v * 2));
  const ink = useTransform(t, (v) => clamp((v - 0.45) / 0.4));
  // Fully drained: out of the accessibility tree and the page's text.
  const visibility = useTransform(t, (v) => (v < 0.01 ? "hidden" : "visible"));

  return (
    <motion.span
      aria-hidden
      data-open={open || undefined}
      style={{ height, scaleX, y, opacity, visibility }}
      className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 grid w-max -translate-x-1/2 origin-bottom place-items-center overflow-hidden rounded-full bg-ink px-2.5 text-xs leading-4 font-medium whitespace-nowrap text-background"
    >
      <motion.span style={{ opacity: ink }}>{text}</motion.span>
    </motion.span>
  );
}
