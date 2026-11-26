// Most reported organisations: who appears in the most events over the last 30 days, by count
// of events, never by clicks or engagement. Empty until issue #15 gives it a data source.
import { lettermark } from "@/components/feed/event-tile";

import type { OrganisationFigure } from "./types";

export function MostReported({ items }: { items: OrganisationFigure[] | null }) {
  if (!items || items.length === 0) {
    return (
      <p className="text-[13px] leading-[18px] text-ink-3">
        No figures yet. Counts appear once events are tallied by organisation.
      </p>
    );
  }
  const max = Math.max(...items.map((i) => i.count));
  return (
    <ol className="flex flex-col gap-2.5">
      {items.slice(0, 5).map((org) => (
        <li key={org.name} className="grid grid-cols-[20px_minmax(0,1fr)_auto] items-center gap-x-2.5">
          <span aria-hidden className="grid size-5 place-items-center rounded-[2px] bg-background text-ink">
            {org.logo ? (
              <svg viewBox="0 0 24 24" className="size-3 fill-current">
                <path d={org.logo.path} />
              </svg>
            ) : (
              <span className="text-[11px] leading-none font-bold">{lettermark(org.name)}</span>
            )}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-[13px] leading-[18px] text-ink">{org.name}</span>
            <span aria-hidden className="mt-1 block h-0.5 bg-rule">
              <span
                className="block h-full bg-ink-3"
                style={{ width: `${(org.count / max) * 100}%` }}
              />
            </span>
          </span>
          <span className="font-mono text-xs text-ink-2 tabular">
            {org.count}
            <span className="sr-only"> events</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
