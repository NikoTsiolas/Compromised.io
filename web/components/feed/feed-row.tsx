// One event in the feed. Desktop: [time gutter] [content] [trust column], divided by hairlines,
// no cards (NYT "Latest", Matter, Canny on Mobbin). Phone: one column with the time on top
// (Perplexity iOS). Every string from the API is rendered as React text, never as HTML.
import { ArrowUpRight } from "lucide-react";

import { TechnicalDetails } from "@/components/feed/technical-details";
import { Trust } from "@/components/feed/trust";
import { Item } from "@/components/ui/item";
import { categoryLabel, formatClock, type FeedItem } from "@/lib/feed";
import { formatOriginal, formatRelative } from "@/lib/time";

export function FeedRow({ item, now }: { item: FeedItem; now?: Date }) {
  const headingId = `event-${item.id}-headline`;
  const relative = formatRelative(item.publishedAt, now);
  const others = item.sources.length - 1;

  return (
    <Item
      render={<article aria-labelledby={headingId} />}
      className="grid grid-cols-1 items-start gap-0 rounded-none border-0 px-0 py-3.5 sm:grid-cols-[72px_minmax(0,1fr)] sm:gap-x-6 sm:py-4 lg:grid-cols-[88px_minmax(0,1fr)_200px]"
    >
      {/* time gutter; on phones it becomes the line above the kicker */}
      <p className="mb-1.5 flex items-baseline gap-2 font-mono text-xs leading-4 text-ink-3 sm:mb-0 sm:flex-col sm:gap-0.5 sm:pt-[3px]">
        <time
          dateTime={item.publishedAt}
          title={formatOriginal(item.publishedAt)}
          className="text-ink"
        >
          {formatClock(item.publishedAt)}
          <span className="text-ink-3"> UTC</span>
        </time>
        <span aria-hidden className="sm:hidden">
          ·
        </span>
        <span>{relative}</span>
      </p>

      <div className="min-w-0">
        <Kicker item={item} />

        <h3
          id={headingId}
          className="text-[17px] leading-[22px] font-bold tracking-[-0.01em] text-ink text-pretty sm:text-lg sm:leading-6"
        >
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="decoration-1 underline-offset-[3px] hover:underline focus-visible:underline"
          >
            {item.headline}
            <ArrowUpRight
              aria-hidden
              className="ml-0.5 inline size-3.5 align-[-1px] text-ink-3"
            />
          </a>
        </h3>

        <Summary item={item} />

        {item.actionLine && (
          <p className="mt-2 text-[13px] leading-[18px] font-bold text-ink">
            <span className="font-mono text-[11px] font-normal tracking-[0.06em] text-ink-3 uppercase">
              Advice from source{" "}
            </span>
            {item.actionLine}
          </p>
        )}

        <div className="mt-2 lg:hidden">
          <Trust trust={item.trust} layout="inline" />
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px] leading-[18px] text-ink-3">
          <span>
            <span className="text-ink-2">{item.publisher}</span>
            {others > 0 && (
              <span>
                {" "}
                +{others} {others === 1 ? "source" : "sources"}
              </span>
            )}
          </span>
          <span aria-hidden>·</span>
          <TechnicalDetails>
            <Details item={item} />
          </TechnicalDetails>
        </div>
      </div>

      <div className="hidden lg:block lg:pt-[3px]">
        <Trust trust={item.trust} />
      </div>
    </Item>
  );
}

function Kicker({ item }: { item: FeedItem }) {
  const parts = [];
  if (item.live) {
    parts.push(
      <span
        key="live"
        className="font-mono text-[11px] font-bold tracking-[0.06em] text-red-ink uppercase"
      >
        Live
      </span>,
    );
  }
  if (item.organization) {
    parts.push(
      <span key="org" className="text-[13px] font-bold text-ink">
        {item.organization}
      </span>,
    );
  } else if (item.organization === null) {
    parts.push(
      <span key="org" className="text-[13px] text-ink-3">
        Organisation unknown
      </span>,
    );
  }
  if (item.category) {
    parts.push(
      <span
        key="cat"
        className="text-[11px] font-medium tracking-[0.06em] text-ink-3 uppercase"
      >
        {item.categoryName ?? categoryLabel(item.category)}
      </span>,
    );
  }
  if (parts.length === 0) return null;
  return (
    <p className="mb-1 flex flex-wrap items-baseline gap-x-2 leading-4">
      {parts.flatMap((part, i) =>
        i === 0
          ? [part]
          : [
              <span key={`sep-${i}`} aria-hidden className="text-ink-3">
                ·
              </span>,
              part,
            ],
      )}
    </p>
  );
}

function Summary({ item }: { item: FeedItem }) {
  if (item.summary) {
    return (
      <p className="mt-1.5 max-w-[68ch] text-[15px] leading-[22px] text-ink-2">
        <span className="mr-1.5 font-mono text-[11px] tracking-[0.06em] text-ink-3 uppercase">
          AI summary
        </span>
        {item.summary}
      </p>
    );
  }
  if (item.excerpt) {
    // The publisher's own words, until a plain-language summary exists. Not labelled as AI.
    return (
      <p className="mt-1.5 line-clamp-2 max-w-[68ch] text-[15px] leading-[22px] text-ink-2">
        {item.excerpt}
      </p>
    );
  }
  return null;
}

function Details({ item }: { item: FeedItem }) {
  return (
    <dl className="mt-3 mb-1 grid grid-cols-1 gap-x-6 gap-y-2 border-t border-rule pt-3 text-[13px] leading-[18px] sm:grid-cols-[140px_minmax(0,1fr)]">
      <dt className="text-[11px] leading-[18px] font-medium tracking-[0.06em] text-ink-3 uppercase">
        CVE identifiers
      </dt>
      <dd className="font-mono text-xs text-ink">
        {item.cves === undefined ? (
          <span className="font-sans text-[13px] text-ink-3">
            Not extracted yet
          </span>
        ) : item.cves.length === 0 ? (
          <span className="font-sans text-[13px] text-ink-3">None named</span>
        ) : (
          item.cves.join(", ")
        )}
      </dd>

      <dt className="text-[11px] leading-[18px] font-medium tracking-[0.06em] text-ink-3 uppercase">
        Attack vector
      </dt>
      <dd className={item.attackVector ? "text-ink" : "text-ink-3"}>
        {item.attackVector ?? "Not identified yet"}
      </dd>

      <dt className="text-[11px] leading-[18px] font-medium tracking-[0.06em] text-ink-3 uppercase">
        Category
      </dt>
      <dd className={item.category ? "text-ink" : "text-ink-3"}>
        {item.category ? (
          <>
            {item.categoryName ?? categoryLabel(item.category)}{" "}
            <span className="font-mono text-xs text-ink-3">
              {item.category}
            </span>
          </>
        ) : (
          "Not classified yet"
        )}
      </dd>

      <dt className="text-[11px] leading-[18px] font-medium tracking-[0.06em] text-ink-3 uppercase">
        Sources
      </dt>
      <dd>
        <ol className="flex flex-col gap-2">
          {item.sources.map((source) => (
            <li key={source.url} className="flex flex-col gap-0.5">
              <span className="font-mono text-xs text-ink-3">
                <time dateTime={source.publishedAt}>
                  {formatOriginal(source.publishedAt)}
                </time>
                {" · "}
                {source.publisher}
              </span>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-ink underline decoration-rule decoration-1 underline-offset-[3px] hover:decoration-ink"
              >
                {source.headline}
              </a>
            </li>
          ))}
        </ol>
      </dd>
    </dl>
  );
}
