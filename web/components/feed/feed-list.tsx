// A list of events as feed rows, divided by hairlines, with an empty state and a link to the
// next page. Shared by the homepage feed and the search results, so both show events the same
// way and a change to how the feed lists events reaches both.
import Link from "next/link";

import { ArrivalItem } from "@/components/bencho-pro/text-fade/arrival-fade";
import { FeedRow } from "@/components/feed/feed-row";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator";
import type { FeedItem } from "@/lib/feed";

export function FeedList({
  items,
  now,
  empty,
  more,
}: {
  items: FeedItem[];
  now?: Date;
  /** Shown instead of the list when there are no items; nothing is shown when omitted. */
  empty?: { title: string; description: string };
  /** The next page, when there is one. */
  more?: { href: string; label: string };
}) {
  return (
    <>
      {items.length === 0 ? (
        empty && <FeedEmpty {...empty} />
      ) : (
        <ol>
          {items.map((item, i) => (
            <ArrivalItem key={item.id} id={item.id}>
              {i > 0 && <Separator className="bg-rule" />}
              <FeedRow item={item} now={now} />
            </ArrivalItem>
          ))}
        </ol>
      )}
      {more && (
        <div className="mt-2 border-t border-rule-strong pt-4">
          <Link
            href={more.href}
            className="text-sm font-medium text-ink underline decoration-1 underline-offset-4"
          >
            {more.label}
          </Link>
        </div>
      )}
    </>
  );
}

function FeedEmpty({ title, description }: { title: string; description: string }) {
  return (
    <Empty className="items-start rounded-none border-0 px-0 py-12 text-left md:py-16">
      <EmptyHeader className="items-start text-left">
        <EmptyTitle className="text-lg font-bold tracking-[-0.01em] text-ink">
          {title}
        </EmptyTitle>
        <EmptyDescription className="max-w-[52ch] text-[15px] leading-[22px] text-ink-2">
          {description}
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}
