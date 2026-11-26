// Measures WCAG 2 contrast ratios of the colour tokens in app/globals.css, light and dark.
//   node scripts/contrast.mjs
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

function tokens(selector) {
  const block = css.match(new RegExp(`${selector} \\{([^}]*)\\}`))[1];
  return Object.fromEntries(
    [...block.matchAll(/--(c-[\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]),
  );
}

function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// [foreground, background, what it is, minimum]
const PAIRS = [
  ["c-ink", "c-bg", "Headlines, organisation, body", 4.5],
  ["c-ink-2", "c-bg", "Summaries, excerpts", 4.5],
  ["c-ink-3", "c-bg", "Metadata, timestamps, tabs", 4.5],
  ["c-ink-3", "c-surface", "Metadata on surfaces", 4.5],
  ["c-accent", "c-bg", "LIVE kicker, attacker-claim label", 4.5],
  ["c-accent", "c-accent-soft", "Sample data banner label", 4.5],
  ["c-ink", "c-accent-soft", "Sample data banner text", 4.5],
  ["c-bg", "c-ink", "New-events bar text", 4.5],
  ["c-rule-strong", "c-bg", "Section and day rules (non-text)", 3],
];

const light = tokens(":root");
const dark = { ...light, ...tokens("\\.dark") };
let failed = 0;
console.log("| Pair | Use | Light | Dark | Needs |");
console.log("|---|---|---|---|---|");
for (const [fg, bg, use, min] of PAIRS) {
  const l = ratio(light[fg], light[bg]);
  const d = ratio(dark[fg], dark[bg]);
  if (l < min || d < min) failed++;
  const mark = (v) => `${v.toFixed(2)}:1${v < min ? " FAIL" : ""}`;
  console.log(`| \`${fg}\` on \`${bg}\` | ${use} | ${mark(l)} | ${mark(d)} | ${min}:1 |`);
}
process.exit(failed ? 1 : 0);
