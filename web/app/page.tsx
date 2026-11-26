// Deliberately bare: the walking skeleton proves data reaches the page. Design is #9.
// Everything from the API is rendered as React text children, never as HTML.
import Link from "next/link";
import { Suspense } from "react";

import { IngestionIndicator, SourceHealthList } from "@/components/ingestion-status";
import { listEvents, listTabs, type EventPage, type Tab } from "@/lib/api";
import { formatOriginal, formatRelative } from "@/lib/time";

const DEFAULT_TAB = "all";

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <>
      <header>
        <h1>Compromised</h1>
        <Suspense fallback={null}>
          <IngestionIndicator />
        </Suspense>
      </header>
      <main>
        <Suspense fallback={<p>Loading events…</p>}>
          <Feed searchParams={searchParams} />
        </Suspense>
        <section aria-labelledby="sources-heading">
          <h2 id="sources-heading">Sources</h2>
          <Suspense fallback={null}>
            <SourceHealthList />
          </Suspense>
        </section>
      </main>
    </>
  );
}

function tabHref(tab: string, cursor?: string) {
  const query: Record<string, string> = {};
  if (tab !== DEFAULT_TAB) query.tab = tab;
  if (cursor) query.cursor = cursor;
  return { pathname: "/", query };
}

async function Feed({
  searchParams,
}: {
  searchParams: PageProps<"/">["searchParams"];
}) {
  const { cursor, tab: requested } = await searchParams;
  let tabs: Tab[];
  let page: EventPage;
  let tab = DEFAULT_TAB;
  try {
    tabs = await listTabs();
    if (typeof requested === "string" && tabs.some((t) => t.id === requested)) {
      tab = requested;
    }
    page = await listEvents(
      tab,
      typeof cursor === "string" ? cursor : undefined,
    );
  } catch {
    return <p>Events could not be loaded.</p>;
  }

  return (
    <>
      <nav aria-label="Feed tabs">
        <ul>
          {tabs.map((t) => (
            <li key={t.id}>
              <Link
                href={tabHref(t.id)}
                aria-current={t.id === tab ? "page" : undefined}
              >
                {t.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      {page.events.length === 0 ? (
        <p>No events yet.</p>
      ) : (
        <ul aria-label="Events">
          {page.events.map((event) => {
            const source = event.sources[0];
            return (
              <li key={event.id}>
                {event.affected_organization}
                {" · "}
                {event.category_label}
                {" — "}
                <a href={source.url} target="_blank" rel="noopener noreferrer">
                  {event.title}
                </a>
                {" — "}
                {source.publisher}
                {" — "}
                <time dateTime={event.published_at}>
                  {formatOriginal(event.published_at)}
                </time>
                {" ("}
                {formatRelative(event.published_at)}
                {")"}
                {event.source_count > 1 && (
                  <details>
                    <summary>{event.source_count} sources</summary>
                    <ul aria-label="Other sources">
                      {event.sources.slice(1).map((other) => (
                        <li key={other.record_id}>
                          <a
                            href={other.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {other.publisher}: {other.headline}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {page.next_cursor && (
        <Link href={tabHref(tab, page.next_cursor)}>Older events</Link>
      )}
    </>
  );
}
