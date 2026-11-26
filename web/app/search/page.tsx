// Search results (#10): the header's search and the phone tab bar's Search (#16) land here. The
// page only places shared parts: the masthead, the search form, then the results as the same
// list Featured uses (FeedList, one FeedRow per event), so a change to how events are listed
// reaches search too; the tab bar below 1024px. Everything from the API is rendered as text.
import type { Metadata } from "next";
import { Suspense, ViewTransition } from "react";

import { BottomTabBar } from "@/components/bencho-pro/bottom-tab-bar";
import { FeedRowsSkeleton } from "@/components/bencho-pro/home-skeleton";
import { FeedList } from "@/components/feed/feed-list";
import { IngestionIndicator } from "@/components/ingestion-status";
import { SearchForm } from "@/components/site/search-form";
import { SiteHeader } from "@/components/site/site-header";
import {
  getFilters,
  RefusedSearch,
  SEARCH_KEYS,
  searchEvents,
  type EventPage,
  type SearchFilters,
  type SearchQuery,
} from "@/lib/api";
import { toFeedItem } from "@/lib/feed";
import { withLogo } from "@/lib/logos";

export const metadata: Metadata = { title: "Search · Compromised" };

// Featured's section heading ("Latest").
const H2 =
  "mt-8 border-b border-rule-strong pb-2 font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase";

type Params = Awaited<PageProps<"/search">["searchParams"]>;

export default function SearchPage({ searchParams }: PageProps<"/search">) {
  return (
    <>
      <SiteHeader
        status={
          <Suspense fallback={null}>
            <IngestionIndicator />
          </Suspense>
        }
      />
      {/* Below 1024px the page keeps room for the tab bar, so it never covers a result. */}
      <main className="mx-auto max-w-[1240px] px-4 pt-6 pb-28 sm:px-6 sm:pt-8 lg:px-10 lg:pb-16">
        <h1 className="sr-only">Search</h1>
        <Suspense fallback={<FormSkeleton />}>
          <Form searchParams={searchParams} />
        </Suspense>
        <section aria-label="Search results">
          <Suspense
            fallback={
              <ViewTransition exit="auto" default="none">
                <div aria-busy="true" aria-label="Loading results">
                  <div className={H2}>&nbsp;</div>
                  <FeedRowsSkeleton />
                </div>
              </ViewTransition>
            }
          >
            <ViewTransition enter="auto" default="none">
              <Results searchParams={searchParams} />
            </ViewTransition>
          </Suspense>
        </section>
      </main>
      <BottomTabBar current="search" />
    </>
  );
}

/** The query and filters as the URL gives them: single strings only, empty ones dropped. */
function queryFrom(params: Params): SearchQuery {
  const query: SearchQuery = {};
  for (const key of [...SEARCH_KEYS, "cursor"] as const) {
    const value = params[key];
    if (typeof value === "string" && value.trim()) query[key] = value.trim();
  }
  return query;
}

function href(query: SearchQuery) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) if (value) params.set(key, value);
  return params.size ? `/search?${params}` : "/search";
}

async function Form({ searchParams }: { searchParams: PageProps<"/search">["searchParams"] }) {
  const query = queryFrom(await searchParams);
  let filters: SearchFilters | null = null;
  try {
    filters = await getFilters();
  } catch {
    // The query alone still works without the filter lists.
  }
  const filtered = SEARCH_KEYS.some((k) => k !== "q" && query[k]);
  return (
    <SearchForm
      // A new search remounts the form, so its fields show what the URL now says.
      key={href({ ...query, cursor: undefined })}
      query={query}
      filters={filters}
      clearHref={filtered ? href({ q: query.q }) : undefined}
    />
  );
}

async function Results({ searchParams }: { searchParams: PageProps<"/search">["searchParams"] }) {
  const query = queryFrom(await searchParams);
  let page: EventPage;
  try {
    page = await searchEvents(query);
  } catch (error) {
    return (
      <p className="py-12 text-[15px] text-ink-2">
        {error instanceof RefusedSearch
          ? "Those filters could not be applied. Clear them and try again."
          : "Search is unavailable right now. Please try again in a minute."}
      </p>
    );
  }
  const items = page.events.map(toFeedItem).map(withLogo);
  return (
    <div>
      <h2 className={H2}>{query.q ? `Results for “${query.q}”` : "All events"}</h2>
      <FeedList
        items={items}
        empty={{
          title: "No events match",
          description:
            "Try another spelling, fewer words or fewer filters. Search covers the events shown in the feed's tabs.",
        }}
        more={
          page.next_cursor
            ? { href: href({ ...query, cursor: page.next_cursor }), label: "More results" }
            : undefined
        }
      />
    </div>
  );
}

/** The form's height while it streams in (field, then one to three rows of filters). */
function FormSkeleton() {
  return (
    <div aria-hidden>
      <div className="h-11" />
      <div className="mt-4 h-[198px] sm:h-[128px] lg:h-[58px]" />
    </div>
  );
}
