// Masthead: wordmark left; live status, search and theme right. A 1px rule beneath (the section
// tabs below carry the heavy 2px rule, NYT / FT style).
import { Search } from "lucide-react";
import Link from "next/link";

import { LiveStatus, type IngestionStatus } from "@/components/site/live-status";
import { SearchField } from "@/components/site/search-field";
import { ThemeSwitch } from "@/components/site/theme-switch";
import { Wordmark } from "@/components/site/wordmark";

export function SiteHeader({
  status = { state: "unknown" },
}: {
  status?: IngestionStatus;
}) {
  return (
    <header className="border-b border-rule">
      <div className="mx-auto flex max-w-[1120px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-10">
        <Wordmark />
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="hidden md:block">
            <LiveStatus status={status} />
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
      <div className="mx-auto max-w-[1120px] px-4 pb-3 sm:px-6 md:hidden">
        <LiveStatus status={status} />
      </div>
    </header>
  );
}
