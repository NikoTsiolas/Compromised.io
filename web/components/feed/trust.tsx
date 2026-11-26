// The trust label, its 0-100 score and the sources it counted, as one component so the score can
// never appear alone (docs/wiki/trust-labels-and-score.md). The wording is the API's `trust.label`,
// shown as sent: the page never derives a label from the status, because who confirmed an event
// (the company, a government agency, security researchers) is known only to the API. Statuses
// differ by glyph and wording, not by hue; the muted red is reserved for attacker claims.
import { Badge } from "@/components/ui/badge";
import type { Trust as TrustValue } from "@/lib/feed";
import { cn } from "@/lib/utils";

export function Trust({
  trust,
  className,
}: {
  /**
   * `null` or `undefined`: the API sent no trust, as for commentary (a newsletter or podcast is
   * not an incident). Nothing is shown in its place: no label, no score, no placeholder.
   */
  trust?: TrustValue | null;
  className?: string;
}) {
  if (!trust) return null;

  const { status, label, score, sources } = trust;
  const claimed = status === "claimed";

  // Inline text, so a long label or source list wraps like a sentence on narrow screens.
  return (
    <p
      data-slot="trust"
      data-status={status}
      aria-label="Trust"
      className={cn("text-[13px] leading-[18px] text-ink-3", className)}
    >
      <Badge
        variant="outline"
        className={cn(
          "inline h-auto whitespace-normal border-0 p-0 text-left align-baseline text-[13px] leading-[18px] font-medium",
          claimed ? "text-red-ink" : "text-ink",
          status === "investigating" && "text-ink-2",
          status === "disputed" && "text-ink-2 line-through decoration-1",
        )}
      >
        <span aria-hidden className="trust-glyph mr-1.5 align-[0px]" data-status={status} />
        {label}
      </Badge>
      <Separator />
      <span
        className="whitespace-nowrap font-mono"
        aria-label={`Confidence score ${score} out of 100`}
      >
        <span className="text-[15px] leading-4 font-bold text-ink tabular">{score}</span>
        <span className="text-xs leading-4">/100</span>
      </span>
      <Separator />
      <span>
        Sources: <span className="text-ink-2">{sources.join(", ")}</span>
      </span>
    </p>
  );
}

/** A middle dot between the parts; spaced so the text reads "label · 70/100 · Sources: …". */
function Separator() {
  return (
    <span aria-hidden className="text-ink-3">
      {" · "}
    </span>
  );
}
