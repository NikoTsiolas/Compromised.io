// Measures WCAG 2 contrast ratios of the colour tokens in app/globals.css, light and dark.
//   node scripts/contrast.mjs
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

// Every block for the selector (globals.css declares :root and .dark more than once).
function tokens(selector) {
  const blocks = [...css.matchAll(new RegExp(`(?:^|\\n)${selector} \\{([^}]*)\\}`, "g"))];
  return Object.fromEntries(
    blocks.flatMap((b) =>
      [...b[1].matchAll(/--((?:c|tile)-[\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]),
    ),
  );
}

const hex = (rgb) => "#" + rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
/** CSS color-mix(in srgb, a p%, b). */
const mix = (a, p, b) => hex(rgb(a).map((v, i) => (v * p + rgb(b)[i] * (100 - p)) / 100));

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
  ["c-ink", "c-surface", "Widget titles and values", 4.5],
  ["c-ink-2", "c-surface", "Chart labels, widget text", 4.5],
  ["c-accent", "c-surface", "Spike columns (non-text)", 3],
  ["chart-grey", "c-surface", "Other chart columns (non-text)", 3],
  ["chip-text", "chip-worst", "Image credit on the lightest picture", 4.5],
  ...[1, 2, 3, 4, 5].flatMap((n) => [
    ["c-ink", `tile-${n}`, `Tile ${n}: logo or lettermark`, 3],
    ["c-ink-2", `tile-${n}`, `Tile ${n}: organisation caption`, 4.5],
  ]),
];

const light = tokens(":root");
const dark = { ...light, ...tokens("\\.dark") };
// Derived colours, computed the way the CSS computes them.
// Chart columns (.xchart-bar): de-emphasis grey on the widget surface, a separate step per
// theme (globals.css --chart-grey).
light["chart-grey"] = mix(light["c-ink"], 48, light["c-surface"]);
dark["chart-grey"] = mix(dark["c-ink"], 38, dark["c-surface"]);
for (const t of [light, dark]) {

  // Image credit chip: #111111 at 75% over the lightest possible picture (white).
  t["chip-worst"] = mix("#111111", 75, "#ffffff");
  t["chip-text"] = "#f6f5f1";
}
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
