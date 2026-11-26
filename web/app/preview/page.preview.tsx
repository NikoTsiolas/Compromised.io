// Design preview with SAMPLE DATA: the homepage components with every field that later tickets
// fill (organisation, plain-language summary, category, trust label and score, extra sources,
// CVEs, action line) populated by invented values. A banner on every screen says so.
// Built only in development or with SAMPLE_PREVIEW=1 (see next.config.ts), never in production.
import type { Metadata } from "next";

import { FeedView } from "@/components/feed/feed-view";
import { SiteHeader } from "@/components/site/site-header";

import { SAMPLE_ITEMS, SAMPLE_NOW } from "./sample-events";

export const metadata: Metadata = {
  title: "Sample data preview · Compromised",
  robots: { index: false, follow: false },
};

export default function SamplePreview() {
  return (
    <>
      <div
        role="note"
        aria-label="Sample data notice"
        className="sticky top-0 z-20 border-b-2 border-red-ink bg-red-soft"
      >
        <p className="mx-auto max-w-[1120px] px-4 py-2 text-[13px] leading-[18px] text-ink sm:px-6 lg:px-10">
          <strong className="mr-2 font-mono text-[11px] font-bold tracking-[0.08em] text-red-ink uppercase">
            Sample data
          </strong>
          Every event on this page is invented to show the design. None of it
          is real.
        </p>
      </div>
      <SiteHeader
        status={{ state: "live", lastCheckedAt: "2026-11-26T14:58:00Z" }}
      />
      <main className="mx-auto max-w-[1120px] px-4 pb-16 sm:px-6 lg:px-10">
        <FeedView
          items={SAMPLE_ITEMS}
          tab="all"
          now={SAMPLE_NOW}
          polling={false}
        />
      </main>
    </>
  );
}
