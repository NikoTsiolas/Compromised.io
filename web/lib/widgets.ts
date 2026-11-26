// The homepage widgets' figures, from the API's /v1/widgets endpoints, in the shapes the widgets
// take. Server-only (logos resolve on the server). A figure that cannot be loaded becomes null,
// so its widget shows its quiet empty state and the rest of the page is unaffected.
import type {
  ExploitedFlaw,
  MonthFigure,
  OrganisationFigure,
} from "@/components/widgets/types";
import {
  getExploitedByMonth,
  getMostReported,
  getRecentlyExploited,
} from "@/lib/api";
import { resolveLogo } from "@/lib/logos";

export type WidgetFigures = {
  frequency: MonthFigure[] | null;
  recentlyExploited: ExploitedFlaw[] | null;
  mostReported: OrganisationFigure[] | null;
};

const orNull = <T,>(p: Promise<T>) => p.catch(() => null);

export async function loadWidgetFigures(): Promise<WidgetFigures> {
  const [history, recent, reported] = await Promise.all([
    orNull(getExploitedByMonth()),
    orNull(getRecentlyExploited()),
    orNull(getMostReported()),
  ]);
  return {
    frequency:
      history?.months.map((m) => ({
        month: m.month,
        count: m.count,
        spike: m.spike,
        notable: m.notable.map((n) => ({
          cve: n.cve,
          title: n.title,
          organization: n.organization,
        })),
      })) ?? null,
    recentlyExploited:
      recent?.items.map((f) => ({ cve: f.cve, product: f.product, addedOn: f.added_on })) ??
      null,
    mostReported:
      reported?.items.map((o) => ({
        name: o.name,
        count: o.count,
        logo: resolveLogo(o.logo_key),
      })) ?? null,
  };
}
