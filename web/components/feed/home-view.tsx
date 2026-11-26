// The homepage below the masthead, shared by the real page and the sample preview so both show
// exactly the same components: section tabs, the new-events slot, then a grid of the featured
// stories, the widget rail and the feed. On desktop the rail runs beside both and can sit on
// either side; below 1024px it stacks between the featured stories and the feed.
import Link from "next/link";
import { ViewTransition } from "react";

import { WidgetRail, type RailWidget } from "@/components/bencho-pro/arrange/widget-rail";
import { NewEventsBar } from "@/components/bencho-pro/new-events-bar";
import { ArrivalItem, MarkSeen } from "@/components/bencho-pro/text-fade/arrival-fade";
import { Featured } from "@/components/feed/featured";
import { FeedRow } from "@/components/feed/feed-row";
import { SectionTabs } from "@/components/feed/section-tabs";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator";
import type { Tab } from "@/lib/api";
import { selectFeatured } from "@/lib/featured";
import { DEFAULT_TAB, type FeedItem } from "@/lib/feed";

export function HomeView({
  items,
  tabs,
  tab,
  withFeatured,
  widgets,
  olderHref,
  now,
  polling = true,
}: {
  items: FeedItem[];
  tabs: Tab[];
  tab: string;
  /** The featured section shows on the first page of the All tab only. */
  withFeatured: boolean;
  widgets: RailWidget[];
  olderHref?: string;
  now?: Date;
  /** Off on the sample preview, which has nothing to poll. */
  polling?: boolean;
}) {
  const newest = items[0];
  const label = tabs.find((t) => t.id === tab)?.label ?? "All";
  const featured = withFeatured
    ? selectFeatured(items, { now })
    : { lead: null, cards: [], rest: items };

  return (
    <>
      <SectionTabs tabs={tabs} active={tab} />
      {polling && (
        <NewEventsBar
          key={newest?.id ?? "none"}
          newestId={newest?.id ?? null}
          newestPublishedAt={newest?.publishedAt ?? null}
        />
      )}
      <MarkSeen ids={items.map((i) => i.id)} />
      <div className="home-grid">
        {/* Switching tabs crossfades the stories; the rail beside them does not move. */}
        <div className="home-featured min-w-0">
          <ViewTransition key={tab} name="home-featured" share="auto" enter="auto" default="none">
            <div>
              {featured.lead && (
                <Featured key={featured.lead.id} featured={featured} now={now} />
              )}
            </div>
          </ViewTransition>
        </div>
        <WidgetRail widgets={widgets} />
        <section aria-label={`${label} events`} className="home-feed min-w-0">
          <ViewTransition key={tab} name="home-feed" share="auto" enter="auto" default="none">
          <div>
          {featured.lead && featured.rest.length > 0 && (
            <h2 className="mt-8 border-b border-rule-strong pb-2 font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase">
              Latest
            </h2>
          )}
          {items.length === 0 ? (
            <FeedEmpty
              title={tab === DEFAULT_TAB ? "No events yet" : `Nothing under ${label} yet`}
              description="Events appear here as soon as sources report them."
            />
          ) : (
            <ol>
              {featured.rest.map((item, i) => (
                <ArrivalItem key={item.id} id={item.id}>
                  {i > 0 && <Separator className="bg-rule" />}
                  <FeedRow item={item} now={now} />
                </ArrivalItem>
              ))}
            </ol>
          )}
          {olderHref && (
            <div className="mt-2 border-t border-rule-strong pt-4">
              <Link
                href={olderHref}
                className="text-sm font-medium text-ink underline decoration-1 underline-offset-4"
              >
                Older events
              </Link>
            </div>
          )}
          </div>
          </ViewTransition>
        </section>
      </div>
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
