// The Feed tab (#16) with SAMPLE DATA: the same FeedView as /feed, filled with the invented events
// and widget figures of /preview, under the same banner. Built only in development or with
// SAMPLE_PREVIEW=1 (see next.config.ts), never in production.
import type { Metadata } from "next";

import { FeedView } from "@/components/feed/feed-view";
import { IngestionBadge, SourceList } from "@/components/ingestion-status";
import { SiteHeader } from "@/components/site/site-header";
import { railWidgets } from "@/components/widgets/rail-widgets";
import { withLogo } from "@/lib/logos";

import { SampleBanner } from "../sample-banner";
import { SAMPLE_ITEMS, SAMPLE_NOW, SAMPLE_TABS } from "../sample-events";
import {
  SAMPLE_FREQUENCY,
  SAMPLE_MOST_REPORTED,
  SAMPLE_RECENTLY_EXPLOITED,
  SAMPLE_STATUS,
} from "../sample-widgets";

export const metadata: Metadata = {
  title: "Sample data preview: Feed · Compromised",
  robots: { index: false, follow: false },
};

export default function SampleFeedPreview() {
  return (
    <>
      <SampleBanner />
      <SiteHeader
        current="feed"
        status={
          <IngestionBadge
            status={SAMPLE_STATUS.status}
            lastSuccessAt={SAMPLE_STATUS.last_success_at}
            now={SAMPLE_NOW}
          />
        }
      />
      <main className="mx-auto max-w-[1240px] px-0 sm:px-6 lg:px-10">
        <FeedView
          items={SAMPLE_ITEMS.map(withLogo)}
          tabs={SAMPLE_TABS}
          tab="all"
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
