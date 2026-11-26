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
  layout = "inline",
  className,
}: {
  /**
   * "inline": one sentence that wraps ("label · 70/100 · Sources: ..."). "post": the Feed's
   * layout from Option A, label left and score right on one row, sources beneath. Same text
   * and order either way; only the separators are hidden.
   */
  layout?: "inline" | "post";
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
  const post = layout === "post";

  // Inline text, so a long label or source list wraps like a sentence on narrow screens.
  return (
    <p
      data-slot="trust"
      data-status={status}
      aria-label="Trust"
      data-layout={layout}
      className={cn(
        "text-[13px] leading-[18px] text-ink-3",
        post && "grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4 gap-y-0.5",
        className,
      )}
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
      <Separator hidden={post} />
      <span
        className={cn("whitespace-nowrap font-mono", post && "col-start-2 row-start-1 justify-self-end")}
        aria-label={`Confidence score ${score} out of 100`}
      >
        <span className="text-[15px] leading-4 font-bold text-ink tabular">{score}</span>
        <span className="text-xs leading-4">/100</span>
      </span>
      <Separator hidden={post} />
      <span className={cn(post && "col-span-2")}>
        Sources: <span className="text-ink-2">{sources.join(", ")}</span>
      </span>
    </p>
  );
}

/** A middle dot between the parts; spaced so the text reads "label · 70/100 · Sources: …". */
function Separator({ hidden = false }: { hidden?: boolean }) {
  return (
    <span aria-hidden className={cn("text-ink-3", hidden && "hidden")}>
      {" · "}
    </span>
  );
}
