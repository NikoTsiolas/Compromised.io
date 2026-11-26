// One event in the feed below the featured section: a picture beside the story, divided from
// the next by a hairline. Desktop and tablet put the picture on the left (Perplexity Discover's
// rows on Mobbin); phones put a smaller one on the right of the headline so the text leads.
import { ArrowUpRight } from "lucide-react";

import { ArrivalFade } from "@/components/bencho-pro/text-fade/arrival-fade";
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
  storyImage,
  summaryText,
} from "@/components/feed/story-parts";
import { Trust } from "@/components/feed/trust";
import { Item } from "@/components/ui/item";
import type { FeedItem } from "@/lib/feed";

export function FeedRow({ item, now }: { item: FeedItem; now?: Date }) {
  const headingId = `event-${item.id}-headline`;
  const summary = summaryText(item);

  return (
    <Item
      render={<article aria-labelledby={headingId} />}
      className="grid grid-cols-[minmax(0,1fr)_96px] grid-rows-[auto_1fr] items-start gap-x-4 gap-y-0 rounded-none border-0 px-0 py-4 sm:grid-cols-[200px_minmax(0,1fr)] sm:gap-x-6 sm:py-5"
    >
      <div className="col-start-2 row-start-1 sm:col-start-1 sm:row-span-2">
        <MediaMorph id={item.id}>
          <EventMedia
            image={storyImage(item)}
            logo={item.logo}
            organization={item.organization}
            fallbackLabel={categoryName(item) ?? "Security incident"}
            size="thumb"
            ratio={4 / 3}
          />
        </MediaMorph>
      </div>

      <div className="col-start-1 row-start-1 min-w-0 sm:col-start-2">
        <Kicker item={item} />
        <h3
          id={headingId}
          className="text-[17px] leading-[22px] font-bold tracking-[-0.01em] text-pretty text-ink sm:text-lg sm:leading-6"
        >
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="story-link decoration-1 underline-offset-[3px]"
          >
            <ArrivalFade id={item.id} text={item.headline} />
            <ArrowUpRight
              aria-hidden
              className="ml-0.5 inline size-3.5 align-[-1px] text-ink-3"
            />
          </a>
        </h3>
        <p className="mt-1.5 font-mono text-xs leading-4 text-ink-3">
          <LocalTime iso={item.publishedAt} style="short-relative" now={now} />
          {item.inFeed === false && (
            // Search covers every incident; this one is kept out of every feed tab.
            <>
              <span aria-hidden> · </span>
              <span className="font-sans text-[13px]">Not shown in the feed</span>
            </>
          )}
        </p>
      </div>

      <div className="col-span-2 row-start-2 min-w-0 sm:col-span-1 sm:col-start-2">
        {summary && (
          <p className="mt-2 line-clamp-3 max-w-[68ch] text-[15px] leading-[22px] text-ink-2">
            {summary.ai && <AiLabel />}
            {summary.text}
          </p>
        )}
        <ActionLine item={item} />
        <div className="mt-2.5 flex flex-col gap-1.5 text-[13px] leading-[18px] text-ink-3">
          <Trust trust={item.trust} />
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
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
    </Item>
  );
}
