// Masthead: wordmark left; live status, search and theme right. A 1px rule beneath (the section
// tabs below carry the heavy 2px rule, NYT / FT style).
import { ViewTransition, type ReactNode } from "react";
import { Search } from "lucide-react";
import Link from "next/link";

import { SearchField } from "@/components/site/search-field";
import { ThemeSwitch } from "@/components/bencho-pro/theme-switch";
import { Wordmark } from "@/components/site/wordmark";

export function SiteHeader({
  status,
}: {
  /** The ingestion indicator (components/ingestion-status.tsx), streamed on the real page. */
  status: ReactNode;
}) {
  const indicator = status;
  return (
    // Named, so the masthead holds still while the page under it changes.
    <ViewTransition name="site-header" default="none">
    <header className="border-b border-rule">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-10">
        <Wordmark />
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="hidden md:block">
            {indicator}
          </div>
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
      <div className="mx-auto max-w-[1240px] px-4 pb-3 sm:px-6 md:hidden">
        {indicator}
      </div>
    </header>
    </ViewTransition>
  );
}
