"use client";

// Newly loaded events fade in; everything already on the page when it first loaded does not.
// MarkSeen records every event id the page shows. Rows that mount later with an id it has not
// seen (after the reader presses the "N new events" bar) are new, and their headline fades.
// The first client render always matches the server's (plain text), so hydration is clean.
import { useEffect, useState } from "react";

import { TextFade } from "./text-fade";

const seen = new Set<string>();
let booted = false;

/**
 * Records every event id on the page. On the first load this also ends the boot window; after
 * a refresh its effect runs after the rows have rendered, so new rows are still unseen while
 * they decide whether to fade.
 */
export function MarkSeen({ ids }: { ids: string[] }) {
  useEffect(() => {
    for (const id of ids) seen.add(id);
    if (!booted) {
      const timer = setTimeout(() => {
        booted = true;
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [ids]);
  return null;
}

export function ArrivalFade({ id, text }: { id: string; text: string }) {
  // Decided once, when the row first renders: false during the first page load and its
  // hydration (so it matches the server), true for an event that was not on the page before.
  const [fresh] = useState(() => typeof window !== "undefined" && booted && !seen.has(id));
  return fresh ? <TextFade text={text} /> : <>{text}</>;
}

/**
 * A feed row that arrived after the page loaded opens to its own height and fades in
 * (.arrival in globals.css); rows that were already there render as they are.
 */
export function ArrivalItem({ id, children }: { id: string; children: React.ReactNode }) {
  const [fresh] = useState(() => typeof window !== "undefined" && booted && !seen.has(id));
  return (
    <li className="arrival" data-fresh={fresh || undefined}>
      <div>{children}</div>
    </li>
  );
}
