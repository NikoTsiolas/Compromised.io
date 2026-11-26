"use client";

// The "N new events" bar. Every 60 seconds it asks how many events are newer than the top row
// the reader is looking at. Nothing on the page changes until the bar is pressed: the slot has a
// fixed height whether or not anything is waiting, so rows never move under the reader.
// After the Bencho notify-widget block (Pro licence: used, not redistributed): only its pill and
// its "N new" text swap (AnimatePresence popLayout) are kept; the dropdown card, avatars and bell
// are gone. Restyled as a full-width ink bar with off-white text and square corners.
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import { RollingNumber } from "@/components/feed/rolling-number";

export const POLL_INTERVAL_MS = 60_000;

const OUT = [0.22, 1, 0.36, 1] as const;

export function NewEventsBar({
  newestId,
  newestPublishedAt,
  tab,
}: {
  /** Count only events in this feed tab (the Feed's categories); all events when absent. */
  tab?: string;
  /** The event at the top of what the reader is looking at. */
  newestId: string | null;
  newestPublishedAt: string | null;
}) {
  const router = useRouter();
  const still = useReducedMotion();
  const [count, setCount] = useState(0);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    if (!newestId || !newestPublishedAt) return;
    let cancelled = false;
    const check = async () => {
      try {
        const params = new URLSearchParams({
          id: newestId,
          published_at: newestPublishedAt,
        });
        if (tab) params.set("tab", tab);
        const response = await fetch(`/api/new-events?${params}`, {
          cache: "no-store",
        });
        if (!response.ok) return;
        const body: { count: number } = await response.json();
        if (!cancelled) setCount(body.count);
      } catch {
        // A failed check is retried at the next interval; the feed itself is unaffected.
      }
    };
    const timer = window.setInterval(check, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [newestId, newestPublishedAt, tab]);

  const show = () => {
    startTransition(() => {
      router.refresh();
    });
    setCount(0);
    window.scrollTo({ top: 0, behavior: still ? "auto" : "smooth" });
  };

  return (
    <div
      className={
        count > 0
          ? "sticky top-0 z-10 h-11 border-b border-rule bg-background"
          : "relative h-11 border-b border-rule"
      }
    >
      <AnimatePresence initial={false} mode="popLayout">
        {count > 0 ? (
          <motion.button
            key="bar"
            type="button"
            onClick={show}
            disabled={pending}
            initial={still ? false : { opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, transition: { duration: 0.12 } }}
            transition={{ duration: 0.22, ease: OUT }}
            className="absolute inset-x-0 top-1 flex h-9 w-full cursor-pointer items-center justify-center gap-2 rounded-[2px] bg-ink text-[13px] leading-[18px] font-medium text-background hover:bg-ink-2 focus-visible:outline-offset-2"
          >
            <span>
              <RollingNumber value={count} />{" "}
              {count === 1 ? "new event" : "new events"}
            </span>
            <span aria-hidden className="opacity-60">
              ·
            </span>
            <span className="underline underline-offset-[3px]">Show</span>
          </motion.button>
        ) : (
          <motion.p
            key="quiet"
            initial={false}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.12 } }}
            className="flex h-full items-center font-mono text-[11px] leading-4 tracking-[0.06em] text-ink-3 uppercase"
          >
            {pending ? "Loading new events…" : "Up to date · checks every minute"}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
