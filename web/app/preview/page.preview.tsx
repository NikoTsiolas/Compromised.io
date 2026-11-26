// Design preview with SAMPLE DATA: the homepage components with every field that later tickets
// fill (organisation, plain-language summary, trust label and score, extra sources, CVEs,
// action line, every widget's figures) populated by invented values. A banner on every screen
// says so. Built only in development or with SAMPLE_PREVIEW=1 (see next.config.ts), never in
// production.
import type { Metadata } from "next";

import { HomeView } from "@/components/feed/home-view";
import { IngestionBadge, SourceList } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { railWidgets } from "@/components/widgets/rail-widgets";
import { withLogo } from "@/lib/logos";

import { SAMPLE_ITEMS, SAMPLE_NOW } from "./sample-events";
import {
  SAMPLE_FREQUENCY,
  SAMPLE_MOST_REPORTED,
  SAMPLE_RECENTLY_EXPLOITED,
  SAMPLE_STATUS,
} from "./sample-widgets";

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
        <p className="mx-auto max-w-[1240px] px-4 py-2 text-[13px] leading-[18px] text-ink sm:px-6 lg:px-10">
          <strong className="mr-2 font-mono text-[11px] font-bold tracking-[0.08em] text-red-ink uppercase">
            Sample data
          </strong>
          Every event and figure on this page is invented to show the design. None of it is
          real.
        </p>
      </div>
      <SiteHeader
        current="featured"
        status={
          <IngestionBadge
            status={SAMPLE_STATUS.status}
            lastSuccessAt={SAMPLE_STATUS.last_success_at}
            now={SAMPLE_NOW}
          />
        }
      />
      <main className="mx-auto max-w-[1240px] px-4 pb-16 sm:px-6 lg:px-10">
        <HomeView
          items={SAMPLE_ITEMS.map(withLogo)}
          widgets={railWidgets({
            frequency: SAMPLE_FREQUENCY,
            recentlyExploited: SAMPLE_RECENTLY_EXPLOITED,
            mostReported: SAMPLE_MOST_REPORTED,
            sourceStatus: <SourceList status={SAMPLE_STATUS} now={SAMPLE_NOW} />,
            now: SAMPLE_NOW,
          })}
          now={SAMPLE_NOW}
          polling={false}
        />
      </main>
    </>
  );
}
