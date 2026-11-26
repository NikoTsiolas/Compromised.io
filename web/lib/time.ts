// Times are shown in the reader's own time zone. The server does not know it, so it renders a
// UTC fallback that the browser replaces after hydration (components/feed/local-time.tsx).
// Every function here takes the zone explicitly, so the same code serves both.

const parts = (iso: string, timeZone: string | undefined) =>
  Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
      timeZone,
    })
      .formatToParts(new Date(iso))
      .map((p) => [p.type, p.value]),
  ) as Record<string, string>;

/** "EST", "GMT+1", "UTC". */
export function zoneName(iso: string, timeZone?: string): string {
  if (timeZone === "UTC") return "UTC";
  const name =
    new Intl.DateTimeFormat("en-US", { timeZoneName: "short", timeZone })
      .formatToParts(new Date(iso))
      .find((p) => p.type === "timeZoneName")?.value ?? "";
  return name === "GMT+0" ? "GMT" : name;
}

/** "16:33" */
export function formatClock(iso: string, timeZone?: string): string {
  const p = parts(iso, timeZone);
  return `${p.hour}:${p.minute}`;
}

/** "16:33" today, "25 Nov 16:33" otherwise (both in the given zone). */
export function formatShort(iso: string, now: Date, timeZone?: string): string {
  const p = parts(iso, timeZone);
  const today = parts(now.toISOString(), timeZone);
  const sameDay = p.day === today.day && p.month === today.month && p.year === today.year;
  return sameDay ? `${p.hour}:${p.minute}` : `${p.day} ${p.month} ${p.hour}:${p.minute}`;
}

/** "25 Nov 2026, 16:33 EST" */
export function formatOriginal(iso: string, timeZone?: string): string {
  const p = parts(iso, timeZone);
  return `${p.day} ${p.month} ${p.year}, ${p.hour}:${p.minute} ${zoneName(iso, timeZone)}`;
}

// numeric: "always", so an event 42 hours old reads "1 day ago", never "yesterday".
const relative = new Intl.RelativeTimeFormat("en", { numeric: "always" });
const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 365 * 24 * 3600],
  ["month", 30 * 24 * 3600],
  ["week", 7 * 24 * 3600],
  ["day", 24 * 3600],
  ["hour", 3600],
  ["minute", 60],
];

/** "12 minutes ago", "1 day ago", "just now" */
export function formatRelative(iso: string, now: Date = new Date()): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) {
      return relative.format(Math.trunc(seconds / size), unit);
    }
  }
  return "just now";
}
