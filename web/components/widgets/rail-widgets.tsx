// The widgets beside the feed, in their default order. The homepage passes the API's figures
// (null when they could not be loaded); the sample preview passes invented values.
import type { ReactNode } from "react";

import type { RailWidget } from "@/components/bencho-pro/arrange/widget-rail";

import { ExploitationChart } from "./exploitation-chart";
import { MostReported } from "./most-reported";
import { RecentlyExploited } from "./recently-exploited";
import type { ExploitedFlaw, MonthFigure, OrganisationFigure } from "./types";

export function railWidgets({
  frequency,
  recentlyExploited,
  mostReported,
  sourceStatus,
}: {
  frequency: MonthFigure[] | null;
  recentlyExploited: ExploitedFlaw[] | null;
  mostReported: OrganisationFigure[] | null;
  sourceStatus: ReactNode;
}): RailWidget[] {
  return [
    {
      id: "exploitation",
      title: "Exploited flaws by month",
      description: "Security flaws confirmed as used in attacks, added each month",
      body: <ExploitationChart frequency={frequency} />,
    },
    {
      id: "recently-exploited",
      title: "Recently exploited",
      description: "Newest flaws known to be used in attacks",
      body: <RecentlyExploited items={recentlyExploited} />,
    },
    {
      id: "most-reported",
      title: "Most reported organisations",
      description: "Named in the most events, last 30 days",
      body: <MostReported items={mostReported} />,
    },
    {
      id: "sources",
      title: "Source status",
      description: "When each source was last checked",
      body: sourceStatus,
    },
  ];
}
