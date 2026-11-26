// The featured section, after Perplexity Discover (Mobbin): one lead story with a large picture,
// headline, summary, published time and source count, then a row of three picture cards.
// The lead's headline and summary arrive with the Bencho Text fade; nothing else on the page does.
import { ArrowUpRight } from "lucide-react";

import { ArrivalFade } from "@/components/bencho-pro/text-fade/arrival-fade";
import { TextFade } from "@/components/bencho-pro/text-fade/text-fade";
import { EventMedia } from "@/components/feed/event-media";
import { LocalTime } from "@/components/feed/local-time";
import {
  ActionLine,
  AiLabel,
  categoryName,
  DetailsLink,
  DetailsToggle,
  Kicker,
  MediaMorph,
  SourceNames,
  sourceCount,
  storyImage,
  summaryText,
} from "@/components/feed/story-parts";
import { Trust } from "@/components/feed/trust";
import type { Featured as FeaturedStories } from "@/lib/featured";
import type { FeedItem } from "@/lib/feed";

export function Featured({
  featured,
  now,
}: {
  featured: FeaturedStories;
  now?: Date;
}) {
  const { lead, cards } = featured;
  if (!lead) return null;
  return (
    <section aria-label="Featured" className="pt-6 sm:pt-8">
      <Lead item={lead} now={now} />
      {cards.length > 0 && (
        <ul
          aria-label="More top stories"
          className="mt-6 grid grid-cols-1 gap-y-4 border-t border-rule pt-5 sm:mt-8 sm:grid-cols-3 sm:gap-x-5 sm:gap-y-0 sm:pt-6"
        >
          {cards.map((item) => (
            <li key={item.id} className="min-w-0">
              <Card item={item} now={now} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Lead({ item, now }: { item: FeedItem; now?: Date }) {
  const headingId = `lead-${item.id}-headline`;
  const summary = summaryText(item);
  const count = sourceCount(item);
  // Words in the headline set when the summary starts, so the two read as one arrival.
  const summaryDelay = Math.min(600, item.headline.split(" ").length * 40 + 120);

  return (
    <article
      aria-labelledby={headingId}
      className="grid grid-cols-1 gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] md:gap-8"
    >
      <div className="md:order-2">
        <MediaMorph id={item.id}>
          <EventMedia
            image={storyImage(item)}
            logo={item.logo}
            organization={item.organization}
            fallbackLabel={categoryName(item) ?? "Security incident"}
            size="lead"
            ratio={16 / 10}
            priority
          />
        </MediaMorph>
      </div>
      <div className="min-w-0 md:order-1">
        <Kicker item={item} />
        <h2
          id={headingId}
          className="text-[26px] leading-[30px] font-bold tracking-[-0.02em] text-pretty text-ink sm:text-[32px] sm:leading-[36px]"
        >
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="story-link decoration-2 underline-offset-[5px]"
          >
            <TextFade text={item.headline} />
            <ArrowUpRight
              aria-hidden
              className="ml-1 inline size-5 align-[-2px] text-ink-3"
            />
          </a>
        </h2>
        <p className="mt-3 flex flex-wrap items-center gap-x-2 font-mono text-xs leading-4 text-ink-3">
          <LocalTime iso={item.publishedAt} style="published" now={now} />
          <span aria-hidden>·</span>
          <span>
            {count} {count === 1 ? "source" : "sources"}
          </span>
        </p>
        {summary && (
          <p className="mt-4 line-clamp-5 max-w-[60ch] text-[16px] leading-[24px] text-ink-2">
            {summary.ai && <AiLabel />}
            <TextFade text={summary.text} delay={summaryDelay} step={12} />
          </p>
        )}
        <ActionLine item={item} />
        <div className="mt-4 flex flex-col gap-2 border-t border-rule pt-3 text-[13px] leading-[18px] text-ink-3">
          <Trust trust={item.trust} />
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            {!item.trust && (
              <>
                <SourceNames item={item} />
                <span aria-hidden>·</span>
              </>
            )}
            <DetailsLink item={item} separator="after" />
            <DetailsToggle item={item} />
          </div>
        </div>
      </div>
    </article>
  );
}

function Card({ item, now }: { item: FeedItem; now?: Date }) {
  const headingId = `card-${item.id}-headline`;
  return (
    <article
      aria-labelledby={headingId}
      className="grid grid-cols-[minmax(0,1fr)_96px] gap-x-4 sm:flex sm:flex-col sm:gap-3"
    >
      <div className="col-start-2 row-start-1 sm:order-first">
        <MediaMorph id={item.id}>
          <EventMedia
            image={storyImage(item)}
            logo={item.logo}
            organization={item.organization}
            fallbackLabel={categoryName(item) ?? "Security incident"}
            size="card"
            ratio={16 / 10}
          />
        </MediaMorph>
      </div>
      <div className="col-start-1 row-start-1 min-w-0">
        <Kicker item={item} className="mb-1 flex flex-wrap items-baseline gap-x-2 leading-4" />
        <h3
          id={headingId}
          className="line-clamp-3 text-[16px] leading-[21px] font-bold tracking-[-0.01em] text-pretty text-ink"
        >
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="story-link decoration-1 underline-offset-[3px]"
          >
            <ArrivalFade id={item.id} text={item.headline} />
          </a>
        </h3>
        <p className="mt-2 font-mono text-xs leading-4 text-ink-3">
          <LocalTime iso={item.publishedAt} style="short-relative" now={now} />
        </p>
        {item.summary && (
          <p className="mt-2 line-clamp-4 text-[14px] leading-[20px] text-ink-2">
            <AiLabel />
            {item.summary}
          </p>
        )}
        <ActionLine item={item} />
        <div className="mt-2 flex flex-col gap-1 text-[13px] leading-[18px] text-ink-3">
          <Trust trust={item.trust} />
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <SourceNames item={item} />
            <DetailsLink item={item} separator={item.trust ? undefined : "before"} />
          </div>
        </div>
      </div>
    </article>
  );
}
