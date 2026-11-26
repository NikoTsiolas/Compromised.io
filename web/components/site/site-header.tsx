// Masthead: wordmark and the Featured / Feed destinations left; live status, "How we score",
// search and theme right. A 1px rule beneath. On phones the two destinations sit on a row of
// their own under the wordmark, beside the live status.
import { ViewTransition, type ReactNode } from "react";
import { Search } from "lucide-react";
import Link from "next/link";

import { PrimaryNav, type Destination } from "@/components/site/primary-nav";
import { SearchField } from "@/components/site/search-field";
import { ThemeSwitch } from "@/components/bencho-pro/theme-switch";
import { Wordmark } from "@/components/site/wordmark";

export function SiteHeader({
  status,
  current,
}: {
  /** The ingestion indicator (components/ingestion-status.tsx), streamed on the real page. */
  status?: ReactNode;
  /** Which destination this page is, for the Featured / Feed links. */
  current?: Destination;
}) {
  const indicator = status;
  return (
    // Named, so the masthead holds still while the page under it changes.
    <ViewTransition name="site-header" default="none">
    <header className="border-b border-rule">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-4 pt-4 pb-2 sm:px-6 sm:py-3 lg:px-10">
        <div className="flex items-center gap-8">
          <Wordmark />
          <PrimaryNav current={current} className="hidden sm:block" />
        </div>
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="hidden md:block">
            {indicator}
          </div>
          <Link
            href="/how-we-score"
            className="text-[13px] leading-[18px] font-medium text-ink-2 underline-offset-4 hover:text-ink hover:underline"
          >
            How we score
          </Link>
          <div className="hidden sm:block">
            <SearchField />
          </div>
          <Link
            href="/search"
            aria-label="Search"
            className="grid size-11 place-items-center text-ink-2 sm:hidden"
          >
            <Search aria-hidden className="size-5" strokeWidth={1.75} />
          </Link>
          <ThemeSwitch />
        </div>
      </div>
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-4 sm:px-6 md:hidden">
        <PrimaryNav current={current} className="sm:hidden" />
        <div className="py-2">{indicator}</div>
      </div>
    </header>
    </ViewTransition>
  );
}
