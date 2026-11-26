"use client";

// A post's quiet action row (Option A): how many outlets reported it, Details, Share and Watch.
// Honest signals only: no likes, replies, reposts, followers or views exist here, and none may
// be added. Details opens the technical details in place, above the row (state from the shadcn
// Collapsible, the 0fr -> 1fr opening from the Bencho faq-accordion as in TechnicalDetails).
// With `eventHref` (every real event has a page, #11) the open panel also links to the event's
// own page; nothing else changes. Share uses the Web Share API where the browser has
// it and copies the link otherwise. Watch keeps the company in this browser only
// (lib/watchlist.ts).
import { ArrowUpRight, ChevronDown, Eye, Newspaper, Share } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { GlideTip } from "@/components/bencho-pro/glide-tip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Toggle } from "@/components/ui/toggle";
import { toggleWatch, useWatchlist } from "@/lib/watchlist";
import { cn } from "@/lib/utils";

const action =
  "relative -my-2 inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-[2px] text-[13px] leading-[18px] font-medium text-ink-2 hover:text-ink sm:my-0 sm:min-h-[30px]";

export function PostActions({
  outlets,
  outletWord,
  organization,
  share,
  eventHref,
  details,
}: {
  outlets: number;
  /** "outlet" for news and official sources, "source" when only a claims tracker reported it. */
  outletWord: "outlet" | "source";
  organization: string | null | undefined;
  share: { title: string; url: string };
  /** The event's own page (#11); absent for the sample preview's made-up events. */
  eventHref?: string;
  details: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div
        data-open={open || undefined}
        className="grid grid-rows-[0fr] transition-[grid-template-rows] duration-(--motion-base) ease-(--ease-out) data-open:grid-rows-[1fr]"
      >
        <div className="min-h-0 overflow-hidden">
          <CollapsibleContent>
            <div className="mb-2 rounded-[2px] bg-surface px-4 pt-1 pb-3">
              {details}
              {eventHref && (
                <Link
                  href={eventHref}
                  className="mt-2 inline-flex items-center gap-1 text-[13px] font-medium text-ink underline underline-offset-4"
                >
                  Open the event page
                  <ArrowUpRight aria-hidden className="size-3.5" />
                </Link>
              )}
            </div>
          </CollapsibleContent>
        </div>
      </div>
      <div
        role="group"
        aria-label="Actions"
        className="flex flex-wrap items-center gap-x-6 gap-y-1 sm:gap-x-7"
      >
        <span className={cn(action, "cursor-default hover:text-ink-2")}>
          <Newspaper aria-hidden className="size-4" strokeWidth={1.75} />
          {outlets} {outlets === 1 ? outletWord : `${outletWord}s`}
        </span>
        <CollapsibleTrigger className={cn(action, "group/details")}>
          <ChevronDown
            aria-hidden
            className="size-4 transition-[rotate] duration-(--motion-base) ease-(--ease-out) group-data-[panel-open]/details:rotate-180"
            strokeWidth={1.75}
          />
          {open ? "Hide details" : "Details"}
        </CollapsibleTrigger>
        <ShareButton {...share} />
        {/* On phones Watch sits in the post's header instead (Option C), so the row fits. */}
        {organization && <WatchButton company={organization} className="hidden sm:inline-flex" />}
      </div>
    </Collapsible>
  );
}

type Outcome = "shared" | "copied" | "failed" | null;

function copyWithSelection(text: string): boolean {
  try {
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const ok = document.execCommand("copy");
    field.remove();
    return ok;
  } catch {
    return false;
  }
}

async function shareOrCopy(data: { title: string; url: string }): Promise<Outcome> {
  const nav = navigator as Navigator & {
    share?: (d: ShareData) => Promise<void>;
    canShare?: (d: ShareData) => boolean;
  };
  if (typeof nav.share === "function" && (!nav.canShare || nav.canShare(data))) {
    try {
      await nav.share(data);
      return "shared";
    } catch (e) {
      // The reader closed the share sheet: nothing to say.
      if (e instanceof DOMException && e.name === "AbortError") return null;
    }
  }
  try {
    await navigator.clipboard.writeText(data.url);
    return "copied";
  } catch {
    return copyWithSelection(data.url) ? "copied" : "failed";
  }
}

function ShareButton({ title, url }: { title: string; url: string }) {
  const [outcome, setOutcome] = useState<Outcome>(null);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const press = async () => {
    const result = await shareOrCopy({ title, url });
    if (result === "shared" || result === null) return;
    setOutcome(result);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setOutcome(null), 1800);
  };
  const said = outcome === "copied" ? "Link copied" : outcome === "failed" ? "Could not copy the link" : "";

  return (
    <span className="relative inline-flex">
      <button type="button" onClick={press} className={action}>
        <Share aria-hidden className="size-4" strokeWidth={1.75} />
        Share
      </button>
      <GlideTip text={said || "Link copied"} open={outcome !== null} />
      <span role="status" className="sr-only">
        {said}
      </span>
    </span>
  );
}

export function WatchButton({
  company,
  variant = "quiet",
  className,
}: {
  company: string;
  /** "quiet": in the action row (Option A). "pill": in a phone post's header (Option C). */
  variant?: "quiet" | "pill";
  className?: string;
}) {
  const list = useWatchlist();
  const on = list.includes(company);
  return (
    <Toggle
      pressed={on}
      onPressedChange={() => toggleWatch(company)}
      aria-label={`Watch ${company}`}
      className={cn(
        action,
        "h-auto min-w-0 px-0 hover:bg-transparent aria-pressed:bg-transparent aria-pressed:text-ink focus-visible:ring-0",
        variant === "pill" &&
          "my-0 -mt-1.5 min-h-8 flex-none rounded-full bg-surface px-3 hover:bg-surface aria-pressed:bg-surface before:absolute before:inset-x-0 before:-inset-y-1.5 before:content-['']",
        className,
      )}
    >
      <Eye aria-hidden className="size-4" strokeWidth={on ? 2.5 : 1.75} />
      {/* The space for the longer word is always reserved (by a pseudo-element, so it is not
          read out), and the row never shifts when the word changes. */}
      <span className="grid after:invisible after:col-start-1 after:row-start-1 after:h-0 after:content-['Watching']">
        <span className="col-start-1 row-start-1">{on ? "Watching" : "Watch"}</span>
      </span>
    </Toggle>
  );
}
