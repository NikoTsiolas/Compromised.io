// Data the widgets display. None of these has a real API yet (issue #15 adds one); until then
// the homepage passes null and each widget shows a quiet empty state. The sample preview
// passes invented values under its "Sample data" banner.
import type { Logo } from "@/lib/feed";

/** One month of the exploitation chart. `month` is "YYYY-MM". */
export type MonthFigure = {
  month: string;
  /** Known exploited vulnerabilities added that month. */
  count: number;
  /** A few notable incidents of that month, shown on hover or focus of a spike month. */
  notable?: { title: string; organization?: string }[];
};

/** By sector: one row per month and sector. Designed, not rendered until the owner confirms. */
export type SectorFigure = { month: string; sector: string; count: number };

/** Incidents that took a service offline, per month. Designed, not rendered yet. */
export type OutageFigure = { month: string; count: number };

export type ExploitationView = "frequency" | "sectors" | "outages";

export type ExploitedFlaw = {
  cve: string;
  product: string;
  /** When it was added to the exploited list, ISO date-time. */
  addedAt: string;
};

export type OrganisationFigure = {
  name: string;
  /** Events naming it in the period. */
  count: number;
  logo?: Logo | null;
};
