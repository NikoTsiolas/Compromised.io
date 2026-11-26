// Data the widgets display. The homepage fills them from the API's /v1/widgets endpoints
// (lib/widgets.ts) and passes null when a figure cannot be loaded; each widget shows a quiet
// empty state for null or an empty list. The sample preview passes invented values under its
// "Sample data" banner.
import type { Logo } from "@/lib/feed";

/** One month of the exploitation chart. `month` is "YYYY-MM". */
export type MonthFigure = {
  month: string;
  /** Known exploited vulnerabilities added that month. */
  count: number;
  /**
   * A spike month, decided by the API's stated rule (at least one standard deviation above
   * the average of the months shown), so the chart and the API always agree.
   */
  spike: boolean;
  /** A few notable incidents of that month, shown on hover or focus of a spike month. */
  notable?: { title: string; organization?: string; cve?: string }[];
};

/** By sector: one row per month and sector. Designed, not rendered until the owner confirms. */
export type SectorFigure = { month: string; sector: string; count: number };

/** Incidents that took a service offline, per month. Designed, not rendered yet. */
export type OutageFigure = { month: string; count: number };

export type ExploitationView = "frequency" | "sectors" | "outages";

export type ExploitedFlaw = {
  cve: string;
  product: string;
  /** The day CISA added it to the exploited list, "YYYY-MM-DD" (CISA gives no time of day). */
  addedOn: string;
};

export type OrganisationFigure = {
  name: string;
  /** Events naming it in the period. */
  count: number;
  logo?: Logo | null;
};
