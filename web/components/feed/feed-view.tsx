// The feed below the masthead: section tabs, the new-events slot, rows grouped by day, and the
// link to older events. Shared by the real homepage and the sample-data preview, so both show
// exactly the same components.
import Link from "next/link";

import { FeedRow } from "@/components/feed/feed-row";
import { NewEventsBar } from "@/components/feed/new-events-bar";
import { SectionTabs } from "@/components/feed/section-tabs";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator";
import { groupByDay, TABS, type FeedItem, type TabSlug } from "@/lib/feed";

export function FeedView({
  items,
  tab,
  olderHref,
  now = new Date(),
  polling = true,
}: {
  items: FeedItem[];
  tab: TabSlug;
  olderHref?: string;
  now?: Date;
  /** Off on the sample preview, which has nothing to poll. */
  polling?: boolean;
}) {
  const newest = items[0];
  const label = TABS.find((t) => t.slug === tab)?.label ?? "All";

  return (
    <>
      <SectionTabs active={tab} />
      {polling && (
        <NewEventsBar
          key={newest?.id ?? "none"}
          newestId={newest?.id ?? null}
          newestPublishedAt={newest?.publishedAt ?? null}
        />
      )}
      <section aria-label={`${label} events`}>
        {tab !== "all" ? (
          <FeedEmpty
            title={`Nothing filed under ${label} yet`}
            description="Events are not sorted into sections yet. Until they are, every event appears under All."
          />
        ) : items.length === 0 ? (
          <FeedEmpty
            title="No events yet"
            description="Events appear here as soon as the first sources have been checked."
          />
        ) : (
          groupByDay(items, now).map((group) => (
            <div key={group.key}>
              <h2 className="mt-6 border-b border-rule-strong pb-2 font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase">
                {group.label}
              </h2>
              <ol aria-label={group.label}>
                {group.items.map((item, i) => (
                  <li key={item.id}>
                    {i > 0 && <Separator className="bg-rule" />}
                    <FeedRow item={item} now={now} />
                  </li>
                ))}
              </ol>
            </div>
          ))
        )}
      </section>
      {olderHref && tab === "all" && (
        <div className="mt-2 border-t border-rule-strong pt-4">
          <Link
            href={olderHref}
            className="text-sm font-medium text-ink underline decoration-1 underline-offset-4"
          >
            Older events
          </Link>
        </div>
      )}
    </>
  );
}

function FeedEmpty({ title, description }: { title: string; description: string }) {
  return (
    <Empty className="items-start rounded-none border-0 px-0 py-12 text-left md:py-16">
      <EmptyHeader className="items-start text-left">
        <EmptyTitle className="text-lg font-bold tracking-[-0.01em] text-ink">
          {title}
        </EmptyTitle>
        <EmptyDescription className="max-w-[52ch] text-[15px] leading-[22px] text-ink-2">
          {description}
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}
