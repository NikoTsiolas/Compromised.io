// SAMPLE DATA for the widgets on /preview. Invented figures that exist only to show the design
// populated. The organisations are fictional (Microsoft's sample company names) and CVE numbers
// use the impossible year 0000. Imported only by app/preview/page.preview.tsx.
import type { IngestionStatus } from "@/lib/api";
import type {
  ExploitedFlaw,
  MonthFigure,
  OrganisationFigure,
} from "@/components/widgets/types";

export const SAMPLE_FREQUENCY: MonthFigure[] = [
  { month: "2025-12", count: 14 },
  { month: "2026-01", count: 18 },
  { month: "2026-02", count: 12 },
  {
    month: "2026-03",
    count: 41,
    notable: [
      { organization: "Fabrikam", title: "Home router flaw used to take over devices" },
      { organization: "Contoso Mail", title: "Webmail bug exploited to read inboxes" },
    ],
  },
  { month: "2026-04", count: 16 },
  { month: "2026-05", count: 21 },
  { month: "2026-06", count: 15 },
  { month: "2026-07", count: 19 },
  {
    month: "2026-08",
    count: 37,
    notable: [
      { organization: "Litware Office Suite", title: "Document flaw used in phishing attacks" },
      { organization: "Adatum Messaging", title: "Message preview bug exploited" },
    ],
  },
  { month: "2026-09", count: 17 },
  { month: "2026-10", count: 22 },
  { month: "2026-11", count: 19 },
];

export const SAMPLE_RECENTLY_EXPLOITED: ExploitedFlaw[] = [
  { cve: "CVE-0000-00001", product: "Fabrikam home routers", addedAt: "2026-11-26T13:00:00Z" },
  { cve: "CVE-0000-00007", product: "Litware Office Suite", addedAt: "2026-11-25T17:00:00Z" },
  { cve: "CVE-0000-00011", product: "Contoso Mail", addedAt: "2026-11-24T09:30:00Z" },
  { cve: "CVE-0000-00014", product: "Adatum Messaging", addedAt: "2026-11-22T15:10:00Z" },
];

export const SAMPLE_MOST_REPORTED: OrganisationFigure[] = [
  { name: "Fabrikam", count: 9 },
  { name: "Northwind Pharmacy", count: 6 },
  { name: "Woodgrove Hospital", count: 4 },
  { name: "Tailspin Logistics", count: 3 },
  { name: "Adatum Messaging", count: 2 },
];

const checked = (minutesAgo: number) =>
  new Date(Date.parse("2026-11-26T15:00:00Z") - minutesAgo * 60_000).toISOString();

export const SAMPLE_STATUS: IngestionStatus = {
  status: "live",
  last_success_at: checked(2),
  sources: [
    ["Fabrikam security advisories", "ok", 2],
    ["Sample Wire", "ok", 4],
    ["Example Security News", "ok", 6],
    ["Placeholder Daily", "stale", 95],
    ["Sample claims tracker", "failing", 240],
    ["Demo Government Alerts", "pending", null],
  ].map(([name, state, mins], i) => ({
    id: `sample-${i}`,
    name: name as string,
    tier: "press" as const,
    interval_seconds: 900,
    state: state as IngestionStatus["sources"][number]["state"],
    last_attempt_at: mins === null ? null : checked(mins as number),
    last_success_at: mins === null ? null : checked(mins as number),
    consecutive_failures: state === "failing" ? 3 : 0,
  })),
};
