"use client";

// Section navigation on the shadcn Tabs primitive (line variant), restyled as Swiss underline
// tabs over the heavy 2px rule. Each tab is a real link with its own URL. On phones the row
// scrolls sideways (X Explore and Substack search tabs on Mobbin).
import Link from "next/link";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TABS, type TabSlug } from "@/lib/feed";

export function SectionTabs({ active }: { active: TabSlug }) {
  return (
    <Tabs value={active} className="gap-0">
      <div className="-mx-4 overflow-x-auto px-4 [scrollbar-width:none] sm:mx-0 sm:px-0 [&::-webkit-scrollbar]:hidden">
        <TabsList
          variant="line"
          aria-label="Sections"
          className="h-auto! gap-5 p-0 sm:gap-6"
        >
          {TABS.map((tab) => (
            <TabsTrigger
              key={tab.slug}
              value={tab.slug}
              nativeButton={false}
              render={
                <Link
                  href={tab.slug === "all" ? "/" : `/?tab=${tab.slug}`}
                  scroll={false}
                />
              }
              className="h-11 flex-none rounded-none border-0 px-0 text-sm font-medium text-ink-3 hover:text-ink focus-visible:ring-0 data-active:font-bold data-active:text-ink after:bottom-0! after:h-0.5 after:bg-ink dark:text-ink-3 dark:data-active:text-ink"
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <div aria-hidden className="h-0.5 bg-rule-strong" />
    </Tabs>
  );
}
