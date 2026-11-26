// Placeholder until search lands (#10, built on another branch, which replaces this file):
// the header's search field and the tab bar's Search lead here, so they get a quiet "coming
// soon" instead of a 404.
import type { Metadata } from "next";
import Link from "next/link";

import { BottomTabBar } from "@/components/bencho-pro/bottom-tab-bar";
import { SiteHeader } from "@/components/site/site-header";

export const metadata: Metadata = {
  title: "Search · Compromised",
};

export default function SearchPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-[1240px] px-4 pt-12 pb-28 sm:px-6 lg:px-10">
        <h1 className="text-[26px] leading-[30px] font-bold tracking-[-0.02em] text-ink">
          Search is coming soon
        </h1>
        <p className="mt-3 max-w-[52ch] text-[15px] leading-[22px] text-ink-2">
          Soon you will be able to look up a company or a product here. Until then, every event is
          in the Feed, and Watch keeps the companies you care about in one list.
        </p>
        <Link
          href="/feed"
          className="mt-5 inline-block text-sm font-medium text-ink underline underline-offset-4"
        >
          Go to the Feed
        </Link>
      </main>
      <BottomTabBar current="search" />
    </>
  );
}
