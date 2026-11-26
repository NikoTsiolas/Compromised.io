// The trust label and its 0-100 score, as one component so the score can never appear alone
// (docs/wiki/trust-labels-and-score.md). Statuses differ by glyph and wording, not by hue;
// the muted red is reserved for attacker claims.
import { Badge } from "@/components/ui/badge";
import type { Trust as TrustValue, VerificationStatus } from "@/lib/feed";
import { cn } from "@/lib/utils";

export function trustLabel(status: VerificationStatus, outlets: number): string {
  switch (status) {
    case "confirmed":
      return "Confirmed by the company";
    case "reported":
      return outlets === 1
        ? "Reported by 1 news outlet"
        : `Reported by ${outlets} news outlets`;
    case "claimed":
      return "Claimed by attackers, not confirmed";
    case "investigating":
      return "Under investigation";
    case "disputed":
      return "Disputed";
  }
}

export function Trust({
  trust,
  layout = "stacked",
  className,
}: {
  /** `undefined` or `null`: not scored yet, shown as a quiet empty state. */
  trust?: TrustValue | null;
  layout?: "stacked" | "inline";
  className?: string;
}) {
  if (!trust) {
    return (
      <p
        data-slot="trust"
        className={cn("text-[13px] leading-[18px] text-ink-3", className)}
      >
        Not yet assessed
      </p>
    );
  }

  const { status, score, outlets } = trust;
  const claimed = status === "claimed";
  const label = trustLabel(status, outlets);

  return (
    <div
      data-slot="trust"
      data-status={status}
      className={cn(
        "flex gap-x-2 gap-y-1",
        layout === "stacked"
          ? "flex-col items-start lg:items-end lg:text-right"
          : "flex-row flex-wrap items-center",
        className,
      )}
    >
      <Badge
        variant="outline"
        className={cn(
          "h-auto gap-1.5 whitespace-normal border-0 p-0 text-left text-[13px] leading-[18px] font-medium",
          claimed ? "text-red-ink" : "text-ink",
          status === "investigating" && "text-ink-2",
          status === "disputed" && "text-ink-2 line-through decoration-1",
        )}
      >
        <span aria-hidden className="trust-glyph" data-status={status} />
        {label}
      </Badge>
      <span
        className="inline-flex items-baseline gap-2 font-mono text-ink-3"
        aria-label={`Confidence score ${score} out of 100`}
      >
        <span className="text-[15px] leading-4 font-bold text-ink tabular">
          {score}
        </span>
        <span className="text-xs leading-4">/100</span>
        {layout === "stacked" && (
          <span aria-hidden className="relative h-0.5 w-12 self-center bg-rule">
            <span
              className="absolute inset-y-0 left-0 bg-ink"
              style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
            />
          </span>
        )}
      </span>
    </div>
  );
}
