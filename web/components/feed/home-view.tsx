// The homepage below the masthead, shared by the real page and the sample preview so both show
// exactly the same components: section tabs, the new-events slot, then a grid of the featured
// stories, the widget rail and the feed. On desktop the rail runs beside both and can sit on
// either side; below 1024px it stacks between the featured stories and the feed.
import { ViewTransition } from "react";

import { WidgetRail, type RailWidget } from "@/components/bencho-pro/arrange/widget-rail";
import { NewEventsBar } from "@/components/bencho-pro/new-events-bar";
import { MarkSeen } from "@/components/bencho-pro/text-fade/arrival-fade";
import { Featured } from "@/components/feed/featured";
import { FeedList } from "@/components/feed/feed-list";
import { SectionTabs } from "@/components/feed/section-tabs";
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
          <FeedList
            items={featured.rest}
            now={now}
            // The featured section may hold every item; the empty state is for no items at all.
            empty={items.length === 0 ? emptyFor(tab, label) : undefined}
            more={
              olderHref
                ? { href: olderHref, label: tab === "trending" ? "More trending events" : "Older events" }
                : undefined
            }
          />
          </div>
          </ViewTransition>
        </section>
      </div>
    </>
  );
}

function emptyFor(tab: string, label: string) {
  if (tab === "trending") {
    return {
      title: "Nothing is trending right now",
      description:
        "Trending ranks events by how many independent sources covered them in the last 72 hours.",
    };
  }
  return {
    title: tab === DEFAULT_TAB ? "No events yet" : `Nothing under ${label} yet`,
    description: "Events appear here as soon as sources report them.",
  };
}
