"use client";

// The reader's Watching list (Option C) and the filter it drives. The list lives only in this
// browser (lib/watchlist.ts). With the filter on (`/feed?watching=1`), WatchGate hides every post
// about a company the reader does not watch, and WatchingEmpty explains an empty result. The
// server cannot know the list, so it renders every post and the browser hides the others.
import { X } from "lucide-react";
import Link from "next/link";
import { useId, type ReactNode } from "react";

import { feedHref } from "@/lib/feed-url";
import { unwatch, useWatchlist } from "@/lib/watchlist";

export function WatchingList({
  watching,
  organizations,
}: {
  watching: boolean;
  organizations: string[];
}) {
  const list = useWatchlist();
  const titleId = useId();
  const count = (company: string) => organizations.filter((o) => o === company).length;
  return (
    <section aria-labelledby={titleId} data-watching-list>
      <div className="flex items-baseline justify-between gap-2 px-3">
        <h2
          id={titleId}
          className="font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase"
        >
          Watching
        </h2>
        {list.length > 0 && (
          <Link
            href={watching ? feedHref() : feedHref({ watching: true })}
            scroll={false}
            className="text-xs font-medium text-ink-2 underline-offset-4 hover:text-ink hover:underline"
          >
            {watching ? "Show all" : "Show only these"}
          </Link>
        )}
      </div>
      {list.length === 0 ? (
        <p className="mt-2 px-3 text-[13px] leading-[18px] text-ink-3">
          Press Watch on a post to follow a company here.
        </p>
      ) : (
        <ul aria-label="Watched companies" className="mt-2 flex flex-col">
          {list.map((company) => {
            const n = count(company);
            return (
              <li key={company} className="group flex items-center gap-2 rounded-[2px] px-3 py-1.5 hover:bg-surface">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm leading-5 font-medium text-ink">{company}</p>
                  <p className="font-mono text-[11px] leading-4 text-ink-3">
                    {n === 0 ? "Nothing on this page" : n === 1 ? "1 post on this page" : `${n} posts on this page`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => unwatch(company)}
                  aria-label={`Stop watching ${company}`}
                  className="grid size-8 flex-none cursor-pointer place-items-center rounded-full text-ink-3 hover:bg-background hover:text-ink"
                >
                  <X aria-hidden className="size-4" strokeWidth={1.75} />
                </button>
              </li>
            );
          })}
        </ul>
      )}
      <p className="mt-3 px-3 text-xs leading-4 text-ink-3">
        Kept in this browser only. No account needed.
      </p>
    </section>
  );
}

/** Hides a post about a company the reader does not watch, while the filter is on. */
export function WatchGate({
  active,
  organization,
  children,
}: {
  active: boolean;
  organization: string | null | undefined;
  children: ReactNode;
}) {
  const list = useWatchlist();
  if (active && !(organization && list.includes(organization))) return null;
  return <>{children}</>;
}

export function WatchingEmpty({
  active,
  organizations,
}: {
  active: boolean;
  organizations: string[];
}) {
  const list = useWatchlist();
  if (!active) return null;
  const shown = organizations.some((o) => list.includes(o));
  if (shown) return null;
  return (
    <div className="px-4 py-12 sm:px-5">
      <p className="text-lg font-bold tracking-[-0.01em] text-ink">
        {list.length === 0 ? "You are not watching any company yet" : "Nothing about your companies yet"}
      </p>
      <p className="mt-2 max-w-[52ch] text-[15px] leading-[22px] text-ink-2">
        {list.length === 0
          ? "Press Watch on a post and that company's events collect here. The list is kept in this browser only."
          : "None of the latest events name a company you watch. They will show here when one does."}
      </p>
      <Link
        href={feedHref()}
        className="mt-4 inline-block text-sm font-medium text-ink underline underline-offset-4"
      >
        Back to every post
      </Link>
    </div>
  );
}
