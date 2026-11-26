// The Feed tab below the masthead (#16), shared by the real page and the sample preview: Option
// A's timeline posts inside Option C's shell.
//
//   desktop (1024px up): categories and Watching on the left, posts, widgets on the right
//   tablet (768-1023px): categories and Watching on the left, posts; widgets behind Charts
//   phone: categories as a sideways row, posts; Watching and the widgets behind the tab bar
//
// The tab bar shows below 1024px and the page reserves its height, so it never covers a post.
import Link from "next/link";
import { ViewTransition } from "react";

import { BottomTabBar, type TabBarItem } from "@/components/bencho-pro/bottom-tab-bar";
import { WidgetRail, type RailWidget } from "@/components/bencho-pro/arrange/widget-rail";
import { NewEventsBar } from "@/components/bencho-pro/new-events-bar";
import { ArrivalItem, MarkSeen } from "@/components/bencho-pro/text-fade/arrival-fade";
import { FeedNav } from "@/components/feed/feed-nav";
import { Post } from "@/components/feed/post";
import { SectionTabs } from "@/components/feed/section-tabs";
import { WatchGate, WatchingEmpty, WatchingList } from "@/components/feed/watching";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import type { Tab } from "@/lib/api";
import { DEFAULT_TAB, type FeedItem } from "@/lib/feed";
import { COMING_SOON_TABS, type FeedView as View } from "@/lib/feed-url";

export function FeedView({
  items,
  tabs,
  tab,
  watching = false,
  view = "posts",
  widgets,
  olderHref,
  now,
  polling = true,
}: {
  items: FeedItem[];
  tabs: Tab[];
  tab: string;
  /** Only posts about companies in the reader's Watching list. */
  watching?: boolean;
  /** "charts" shows the widgets in place of the posts below 1024px (the tab bar's Charts). */
  view?: View;
  widgets: RailWidget[];
  olderHref?: string;
  now?: Date;
  /** Off on the sample preview, which has nothing to poll. */
  polling?: boolean;
}) {
  const label = watching ? "Watched" : (tabs.find((t) => t.id === tab)?.label ?? "All");
  const comingSoon = !watching && COMING_SOON_TABS.has(tab);
  const organizations = items.map((i) => i.organization).filter((o): o is string => Boolean(o));
  const newest = items[0];
  const current: TabBarItem = view === "charts" ? "charts" : watching ? "watching" : "feed";
  const activeTab = watching ? null : tab;

  return (
    <div data-view={view} className="feed-page">
      <div className="px-4 sm:px-0 md:hidden">
        <SectionTabs tabs={tabs} active={activeTab} />
      </div>
      <div className="feed-grid">
        <FeedNav
          tabs={tabs}
          active={activeTab}
          watching={watching}
          organizations={organizations}
        />
        <section aria-label={`${label} posts`} className="feed-main min-w-0">
          {watching && (
            <div className="border-b border-rule py-4 md:hidden">
              <WatchingList watching organizations={organizations} />
            </div>
          )}
          {polling && !comingSoon && (
            <NewEventsBar
              key={newest?.id ?? "none"}
              newestId={newest?.id ?? null}
              newestPublishedAt={newest?.publishedAt ?? null}
              tab={watching ? DEFAULT_TAB : tab}
            />
          )}
          <MarkSeen ids={items.map((i) => i.id)} />
          <ViewTransition key={`${tab}-${watching}`} name="feed-posts" share="auto" enter="auto" default="none">
            <div>
              {comingSoon ? (
                <ComingSoon label={label} />
              ) : items.length === 0 ? (
                <Quiet
                  title={tab === DEFAULT_TAB ? "No events yet" : `Nothing under ${label} yet`}
                  description="Events appear here as soon as sources report them."
                />
              ) : (
                <>
                  <ol className="flex flex-col">
                    {items.map((item) => (
                      <WatchGate key={item.id} active={watching} organization={item.organization}>
                        <ArrivalItem id={item.id}>
                          <div className="border-b border-rule">
                            <Post item={item} now={now} />
                          </div>
                        </ArrivalItem>
                      </WatchGate>
                    ))}
                  </ol>
                  <WatchingEmpty active={watching} organizations={organizations} />
                </>
              )}
              {olderHref && !comingSoon && (
                <div className="px-4 py-5 text-center sm:px-5">
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
        <WidgetRail widgets={widgets} sideSwitch={false} />
      </div>
      <BottomTabBar current={current} />
    </div>
  );
}

/** A category another ticket is still building (#10): a quiet note, not a 404. */
function ComingSoon({ label }: { label: string }) {
  return (
    <Quiet
      title={`${label} is coming soon`}
      description="This view is being built. Every event is already in All and the other categories."
    />
  );
}

function Quiet({ title, description }: { title: string; description: string }) {
  return (
    <Empty className="items-start rounded-none border-0 px-4 py-12 text-left sm:px-5 md:py-16">
      <EmptyHeader className="items-start text-left">
        <EmptyTitle role="heading" aria-level={2} className="text-lg font-bold tracking-[-0.01em] text-ink">
          {title}
        </EmptyTitle>
        <EmptyDescription className="max-w-[52ch] text-[15px] leading-[22px] text-ink-2">
          {description}
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}
