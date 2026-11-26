// The Featured tab below the masthead, shared by the real page and the sample preview so both
// show exactly the same components: the new-events slot, then a grid of the featured stories,
// the widget rail and a short list of further top stories (the category tabs live in the Feed
// since #16; the full list is the Feed). On desktop the rail runs beside both and can sit on
// either side; below 1024px it stacks between the featured stories and the feed.
import { ViewTransition } from "react";

import { WidgetRail, type RailWidget } from "@/components/bencho-pro/arrange/widget-rail";
import { NewEventsBar } from "@/components/bencho-pro/new-events-bar";
import { MarkSeen } from "@/components/bencho-pro/text-fade/arrival-fade";
import { Featured } from "@/components/feed/featured";
import { FeedList } from "@/components/feed/feed-list";
import { selectFeatured } from "@/lib/featured";
import type { FeedItem } from "@/lib/feed";
import { FEED_PATH } from "@/lib/feed-url";

/** How many further stories Featured lists below its cards; the Feed has the rest. */
export const FEATURED_LIST_LENGTH = 6;

export function HomeView({
  items,
  widgets,
  now,
  polling = true,
}: {
  items: FeedItem[];
  widgets: RailWidget[];
  now?: Date;
  /** Off on the sample preview, which has nothing to poll. */
  polling?: boolean;
}) {
  const newest = items[0];
  const featured = selectFeatured(items, { now });
  const list = featured.rest.slice(0, FEATURED_LIST_LENGTH);

  return (
    <>
      {polling && (
        <NewEventsBar
          key={newest?.id ?? "none"}
          newestId={newest?.id ?? null}
          newestPublishedAt={newest?.publishedAt ?? null}
        />
      )}
      <MarkSeen ids={items.map((i) => i.id)} />
      <div className="home-grid">
        <div className="home-featured min-w-0">
          <ViewTransition name="home-featured" share="auto" enter="auto" default="none">
            <div>
              {featured.lead && (
                <Featured key={featured.lead.id} featured={featured} now={now} />
              )}
            </div>
          </ViewTransition>
        </div>
        <WidgetRail widgets={widgets} />
        <section aria-label="All events" className="home-feed min-w-0">
          <ViewTransition name="home-feed" share="auto" enter="auto" default="none">
          <div>
          {featured.lead && list.length > 0 && (
            <h2 className="mt-8 border-b border-rule-strong pb-2 font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase">
              Latest
            </h2>
          )}
          <FeedList
            items={list}
            now={now}
            // The featured section may hold every item; the empty state is for no items at all.
            empty={
              items.length === 0
                ? {
                    title: "No events yet",
                    description: "Events appear here as soon as sources report them.",
                  }
                : undefined
            }
            more={
              items.length > 0
                ? { href: FEED_PATH, label: "Every event, newest first, in the Feed" }
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
