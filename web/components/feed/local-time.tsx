"use client";

// A time in the reader's own zone. The server cannot know that zone, so the server render and
// the hydration render both show the same UTC fallback (useSyncExternalStore's server snapshot),
// and the browser swaps in local time straight after. Nothing differs between the two renders,
// so there is no hydration mismatch. Relative times ("4 hours ago") are client-only for the same
// reason, unless a fixed `now` is given (the sample preview).
import { useSyncExternalStore } from "react";

import {
  formatOriginal,
  formatRelative,
  formatShort,
} from "@/lib/time";

const noop = () => () => {};
const useInBrowser = () =>
  useSyncExternalStore(
    noop,
    () => true,
    () => false,
  );

export type TimeStyle =
  /** "16:33" or "25 Nov 16:33" */
  | "short"
  /** "16:33 · 4 hours ago" */
  | "short-relative"
  /** "Published 16:33 · 4 hours ago" */
  | "published"
  /** "25 Nov 2026, 16:33 EST" */
  | "full";

export function LocalTime({
  iso,
  style = "short",
  now,
  className,
}: {
  iso: string;
  style?: TimeStyle;
  /** A fixed "now" for relative times (sample preview); otherwise the browser clock. */
  now?: Date;
  className?: string;
}) {
  const inBrowser = useInBrowser();
  const zone = inBrowser ? undefined : "UTC";
  const reference = now ?? (inBrowser ? new Date() : null);
  const relative = reference ? formatRelative(iso, reference) : null;
  const short = formatShort(iso, reference ?? new Date(iso), zone);

  let text: string;
  switch (style) {
    case "full":
      text = formatOriginal(iso, zone);
      break;
    case "published":
      text = relative ? `Published ${short} · ${relative}` : `Published ${short} UTC`;
      break;
    case "short-relative":
      text = relative ? `${short} · ${relative}` : `${short} UTC`;
      break;
    default:
      text = inBrowser ? short : `${short} UTC`;
  }

  return (
    <time dateTime={iso} title={formatOriginal(iso, zone)} className={className}>
      {text}
    </time>
  );
}
