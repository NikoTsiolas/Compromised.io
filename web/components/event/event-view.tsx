// One event's page (#11), built only from the parts every story already uses (kicker, picture or
// tile, AI summary label, advice from source, trust, technical details) so it reads the same as
// the feed. The page-level layout is a single column and deliberately thin: the feed's layout is
// about to change, and this page should follow it rather than set a look of its own. Every
// string from the API is rendered as React text, never as HTML.
import { ArrowUpRight } from "lucide-react";

import { EventMedia } from "@/components/feed/event-media";
import { LocalTime } from "@/components/feed/local-time";
import {
  ActionLine,
  AiLabel,
  categoryName,
  Kicker,
  MediaMorph,
  summaryText,
  TechnicalFacts,
} from "@/components/feed/story-parts";
import { Trust } from "@/components/feed/trust";
import type { FeedItem } from "@/lib/feed";

// The homepage's section heading ("Latest").
const H2 =
  "mt-10 border-b border-rule-strong pb-2 font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase";

export function EventView({ item }: { item: FeedItem }) {
  const summary = summaryText(item);

  return (
    <article aria-labelledby="event-headline" className="max-w-[720px]">
      <Kicker item={item} />
      <h1
        id="event-headline"
        className="text-[26px] leading-[30px] font-bold tracking-[-0.02em] text-pretty text-ink sm:text-[32px] sm:leading-[36px]"
      >
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="story-link decoration-1 underline-offset-[3px]"
        >
          {item.headline}
          <ArrowUpRight aria-hidden className="ml-1 inline size-5 align-[-2px] text-ink-3" />
        </a>
      </h1>
      <p className="mt-2 font-mono text-xs leading-4 text-ink-3">
        <LocalTime iso={item.publishedAt} style="published" /> · {item.publisher}
      </p>

      <MediaMorph id={item.id}>
        <EventMedia
          image={item.image}
          logo={item.logo}
          organization={item.organization}
          fallbackLabel={categoryName(item) ?? "Security incident"}
          size="lead"
          priority
          className="mt-5"
        />
      </MediaMorph>

      {summary && (
        <p className="mt-5 max-w-[68ch] text-[17px] leading-[26px] text-ink-2">
          {summary.ai && <AiLabel />}
          {summary.text}
        </p>
      )}
      <ActionLine item={item} />
      <Trust trust={item.trust} className="mt-3" />

      <h2 id="event-timeline" className={H2}>
        Timeline
      </h2>
      {/* Every source, in the order they published, at the time they published. */}
      <ol aria-labelledby="event-timeline" className="mt-1">
        {item.sources.map((source) => (
          <li
            key={source.url}
            className="flex flex-col gap-0.5 border-b border-rule py-3 text-[15px] leading-[22px]"
          >
            <span className="font-mono text-xs leading-4 text-ink-3">
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

      <section aria-labelledby="event-technical">
        <h2 id="event-technical" className={H2}>
          Technical details
        </h2>
        <TechnicalFacts item={item} sources={false} className="mt-3" />
      </section>
    </article>
  );
}
