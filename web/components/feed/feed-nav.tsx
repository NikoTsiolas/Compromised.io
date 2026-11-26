// The Feed's left column (Option C's shell, after X's and Reddit's web navigation on Mobbin):
// the seven categories as a vertical list with an icon each, then the reader's Watching list.
// Shown from tablet width up; phones get the categories as a sideways-scrolling row and the
// Watching list behind the bottom tab bar.
import {
  Activity,
  BookOpen,
  Database,
  Download,
  House,
  Lock,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { WatchingList } from "@/components/feed/watching";
import type { Tab } from "@/lib/api";
import { feedHref } from "@/lib/feed-url";
import { cn } from "@/lib/utils";

const ICONS: Record<string, LucideIcon> = {
  all: House,
  breaches: Database,
  ransomware: Lock,
  "under-attack": Activity,
  "update-now": Download,
  research: BookOpen,
  trending: TrendingUp,
};

export function FeedNav({
  tabs,
  active,
  watching,
  organizations,
}: {
  tabs: Tab[];
  /** The category shown, or null while the Watching filter is on. */
  active: string | null;
  watching: boolean;
  /** Companies named on this page, to say how many posts each watched one has here. */
  organizations: string[];
}) {
  return (
    <div className="feed-nav hidden md:block">
      <div className="sticky top-4 flex flex-col gap-5 pt-4">
        <nav aria-label="Categories">
          <ul className="flex flex-col gap-0.5">
            {tabs.map((tab) => {
              const Icon = ICONS[tab.id] ?? House;
              const on = tab.id === active;
              return (
                <li key={tab.id}>
                  <Link
                    href={feedHref({ tab: tab.id })}
                    scroll={false}
                    aria-current={on ? "page" : undefined}
                    className={cn(
                      "flex h-10 items-center gap-3 rounded-full px-3 text-[15px] leading-5 text-ink-2 hover:bg-surface hover:text-ink",
                      on && "bg-surface font-bold text-ink",
                    )}
                  >
                    <Icon aria-hidden className="size-[18px] flex-none" strokeWidth={on ? 2.25 : 1.75} />
                    {tab.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="border-t border-rule pt-4">
          <WatchingList watching={watching} organizations={organizations} />
        </div>
      </div>
    </div>
  );
}
