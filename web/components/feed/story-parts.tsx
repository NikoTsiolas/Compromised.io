// The pieces every story shows, shared by the featured lead, the cards and the feed rows, so
// the trust label, the "AI summary" label, "Advice from source" and the technical details read
// the same wherever an event appears. Every string from the API is rendered as React text.
import Link from "next/link";
import { ViewTransition, type ReactNode } from "react";

import { TechnicalDetails } from "@/components/bencho-pro/technical-details";
import { LocalTime } from "@/components/feed/local-time";
import { eventPath, hasEventPage } from "@/lib/event";
import { categoryLabel, type FeedItem } from "@/lib/feed";
import { cn } from "@/lib/utils";

export function categoryName(item: FeedItem): string | null {
  if (!item.category) return null;
  return item.categoryName ?? categoryLabel(item.category);
}

/** Organisation · CATEGORY, with a red LIVE first for events under active attack. */
export function Kicker({ item, className }: { item: FeedItem; className?: string }) {
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
  const category = categoryName(item);
  if (category) {
    parts.push(
      <span
        key="cat"
        className="text-[11px] font-medium tracking-[0.06em] text-ink-3 uppercase"
      >
        {category}
      </span>,
    );
  }
  if (parts.length === 0) return null;
  return (
    <p className={className ?? "mb-1 flex flex-wrap items-baseline gap-x-2 leading-4"}>
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

/** The plain-language AI summary, labelled; else the publisher's own excerpt, unlabelled. */
export function summaryText(item: FeedItem): { text: string; ai: boolean } | null {
  if (item.summary) return { text: item.summary, ai: true };
  if (item.excerpt) return { text: item.excerpt, ai: false };
  return null;
}

export function AiLabel() {
  return (
    <span className="mr-1.5 font-mono text-[11px] tracking-[0.06em] text-ink-3 uppercase">
      AI summary
    </span>
  );
}

export function ActionLine({ item }: { item: FeedItem }) {
  if (!item.actionLine) return null;
  return (
    <p className="mt-2 text-[13px] leading-[18px] font-bold text-ink">
      <span className="font-mono text-[11px] font-normal tracking-[0.06em] text-ink-3 uppercase">
        Advice from source{" "}
      </span>
      {item.actionLine}
    </p>
  );
}

export function sourceCount(item: FeedItem): number {
  return Math.max(1, item.sources.length);
}

/** "BleepingComputer +2 sources": the publisher always named beside the trust label. */
export function SourceNames({ item }: { item: FeedItem }) {
  const others = item.sources.length - 1;
  return (
    <span>
      <span className="text-ink-2">{item.publisher}</span>
      {others > 0 && (
        <span>
          {" "}
          +{others} {others === 1 ? "source" : "sources"}
        </span>
      )}
    </span>
  );
}

/**
 * The small "Details" link to the event's own page (#11). The headline keeps opening the
 * publisher. Its name is just "Details": every story is an article named by its headline, which
 * gives the link its context (and keeps the headline the only link named after it).
 * Sample events on /preview have no page and show no link.
 */
export function DetailsLink({ item }: { item: FeedItem }) {
  if (!hasEventPage(item.id)) return null;
  return (
    <Link
      href={eventPath(item.id)}
      className="-my-3 inline-flex min-h-11 items-center text-[13px] leading-[18px] text-ink-3 underline-offset-4 hover:text-ink hover:underline sm:my-0 sm:min-h-0"
    >
      Details
    </Link>
  );
}

/**
 * Names an event's picture for view transitions, so following "Details" carries the picture
 * from the story into the event page (the shared motion tokens in globals.css time it).
 */
export function MediaMorph({ id, children }: { id: string; children: ReactNode }) {
  return (
    <ViewTransition name={`event-media-${id}`} share="auto" default="none">
      {children}
    </ViewTransition>
  );
}

export function DetailsToggle({ item }: { item: FeedItem }) {
  return (
    <TechnicalDetails>
      <TechnicalFacts item={item} />
    </TechnicalDetails>
  );
}

/** CVEs, attack vector, category and (unless the page lists them itself) every source. */
export function TechnicalFacts({
  item,
  sources = true,
  className = "mt-3 mb-1 border-t border-rule pt-3",
}: {
  item: FeedItem;
  sources?: boolean;
  /** Spacing and rule above the list; the expand inside a story draws a hairline. */
  className?: string;
}) {
  const term =
    "text-[11px] leading-[18px] font-medium tracking-[0.06em] text-ink-3 uppercase";
  const category = categoryName(item);
  return (
    <dl
      className={cn(
        "grid grid-cols-1 gap-x-6 gap-y-2 text-[13px] leading-[18px] sm:grid-cols-[140px_minmax(0,1fr)]",
        className,
      )}
    >
      <dt className={term}>CVE identifiers</dt>
      <dd className="font-mono text-xs text-ink">
        {item.cves === undefined ? (
          <span className="font-sans text-[13px] text-ink-3">Not extracted yet</span>
        ) : item.cves.length === 0 ? (
          <span className="font-sans text-[13px] text-ink-3">None named</span>
        ) : (
          item.cves.join(", ")
        )}
      </dd>

      <dt className={term}>Attack vector</dt>
      <dd className={item.attackVector ? "text-ink" : "text-ink-3"}>
        {item.attackVector ?? "Not identified yet"}
      </dd>

      <dt className={term}>Category</dt>
      <dd className={category ? "text-ink" : "text-ink-3"}>
        {category ? (
          <>
            {category}{" "}
            <span className="font-mono text-xs text-ink-3">{item.category}</span>
          </>
        ) : (
          "Not classified yet"
        )}
      </dd>

      {sources && (
        <>
      <dt className={term}>Sources</dt>
      <dd>
        <ol className="flex flex-col gap-2">
          {item.sources.map((source) => (
            <li key={source.url} className="flex flex-col gap-0.5">
              <span className="font-mono text-xs text-ink-3">
                <LocalTime iso={source.publishedAt} style="full" />
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
        </>
      )}
    </dl>
  );
}
