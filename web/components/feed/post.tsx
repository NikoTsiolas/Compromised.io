// One event as a Feed post, Option A's anatomy (Figma "Post", node 6:88): the affected company's
// logo or lettermark as avatar; company, category and local time on one line; the original
// headline linking to the publisher; the labelled AI summary; "Advice from source" when there is
// one; the picture; the trust label with score and source names; the quiet action row.
//
// Every post has a picture, all at one size (16:9 across the column): the publisher's photo with
// its credit, or the designed logo / lettermark tile in exactly the same box. Attacker claims
// never show a photo, whatever a source sent; they get the tile.
import { ArrowUpRight } from "lucide-react";

import { ArrivalFade } from "@/components/bencho-pro/text-fade/arrival-fade";
import { CompanyAvatar } from "@/components/feed/company-avatar";
import { EventMedia } from "@/components/feed/event-media";
import { LocalTime } from "@/components/feed/local-time";
import { PostActions, WatchButton } from "@/components/feed/post-actions";
import {
  AiLabel,
  categoryName,
  Details,
  outletCount,
  SourceNames,
  storyImage,
  summaryText,
} from "@/components/feed/story-parts";
import { Trust } from "@/components/feed/trust";
import type { FeedItem } from "@/lib/feed";

export const POST_RATIO = 16 / 9;

export function Post({ item, now }: { item: FeedItem; now?: Date }) {
  const headingId = `post-${item.id}-headline`;
  const summary = summaryText(item);
  const category = categoryName(item);
  const claimed = item.trust?.status === "claimed";
  const onlyClaims = claimed && item.trust?.sources.length === 1;

  return (
    <article
      aria-labelledby={headingId}
      data-organization={item.organization ?? undefined}
      className="flex gap-3 px-4 pt-4 pb-3 sm:px-5"
    >
      <CompanyAvatar organization={item.organization} logo={item.logo} />
      <div className="flex min-w-0 flex-1 flex-col gap-2.5">
        <p className="flex min-w-0 items-baseline gap-1.5 leading-5 whitespace-nowrap">
          {item.organization ? (
            <span className="truncate text-[15px] font-bold text-ink">{item.organization}</span>
          ) : (
            <span className="truncate text-[15px] text-ink-3">Organisation unknown</span>
          )}
          {item.live && (
            <span className="text-[13px] leading-[18px] font-medium text-red-ink">Live</span>
          )}
          {category && (
            <span className="min-w-0 flex-1 truncate text-[13px] leading-[18px] text-ink-3">
              <span aria-hidden>· </span>
              {category}
            </span>
          )}
          {/* Phones show the clock time only; wider screens add how long ago. */}
          <span className="ml-auto flex-none font-mono text-xs leading-4 text-ink-3 sm:hidden">
            <LocalTime iso={item.publishedAt} style="short" now={now} />
          </span>
          <span className="ml-auto hidden flex-none font-mono text-xs leading-4 text-ink-3 sm:inline">
            <LocalTime iso={item.publishedAt} style="short-relative" now={now} />
          </span>
          {item.organization && (
            <WatchButton company={item.organization} variant="pill" className="ml-1 sm:hidden" />
          )}
        </p>

        <h3
          id={headingId}
          className="text-[16px] leading-[22px] font-bold tracking-[-0.01em] text-pretty text-ink"
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

        {summary && (
          <p className="line-clamp-5 text-[15px] leading-[22px] text-ink-2">
            {summary.ai && <AiLabel />}
            {summary.text}
          </p>
        )}

        {item.actionLine && (
          <p className="rounded-[2px] bg-surface px-3 py-2.5 text-[13px] leading-[18px] font-bold text-ink">
            <span className="mr-1.5 font-mono text-[11px] font-normal tracking-[0.06em] text-ink-3 uppercase">
              Advice from source
            </span>
            {item.actionLine}
          </p>
        )}

        <EventMedia
          image={storyImage(item)}
          logo={item.logo}
          organization={item.organization}
          fallbackLabel={category ?? "Security incident"}
          size="post"
          ratio={POST_RATIO}
          className="rounded-[12px]"
        />

        <Trust trust={item.trust} layout="post" />
        {!item.trust && (
          <p className="text-[13px] leading-[18px] text-ink-3">
            <SourceNames item={item} />
          </p>
        )}

        <PostActions
          outlets={outletCount(item)}
          outletWord={onlyClaims ? "source" : "outlet"}
          organization={item.organization}
          share={{ title: item.headline, url: item.url }}
          details={<Details item={item} />}
        />
      </div>
    </article>
  );
}
