// Deliberately bare: the walking skeleton proves data reaches the page. Design is #9.
// Everything from the API is rendered as React text children, never as HTML.
import Link from "next/link";
import { Suspense } from "react";

import { IngestionIndicator, SourceHealthList } from "@/components/ingestion-status";
import { listEvents, type EventPage } from "@/lib/api";
import { formatOriginal, formatRelative } from "@/lib/time";

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

async function Feed({
  searchParams,
}: {
  searchParams: PageProps<"/">["searchParams"];
}) {
  const { cursor } = await searchParams;
  let page: EventPage;
  try {
    page = await listEvents(typeof cursor === "string" ? cursor : undefined);
  } catch {
    return <p>Events could not be loaded.</p>;
  }
  if (page.events.length === 0) {
    return <p>No events yet.</p>;
  }

  return (
    <>
      <ul aria-label="Events">
        {page.events.map((event) => {
          const source = event.sources[0];
          return (
            <li key={event.id}>
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
            </li>
          );
        })}
      </ul>
      {page.next_cursor && (
        <Link href={{ pathname: "/", query: { cursor: page.next_cursor } }}>
          Older events
        </Link>
      )}
    </>
  );
}
