// Header status: whether ingestion is running. Source health arrives with ticket #3; until the
// API reports it, the indicator says so quietly instead of claiming the feed is live.
import { formatClock } from "@/lib/feed";

export type IngestionStatus =
  | { state: "live"; lastCheckedAt: string }
  | { state: "delayed"; lastCheckedAt: string }
  | { state: "unknown" };

export function LiveStatus({ status }: { status: IngestionStatus }) {
  if (status.state === "unknown") {
    return (
      <p className="text-xs leading-4 text-ink-3">
        <span className="sr-only">Ingestion status: </span>Source status not
        reported yet
      </p>
    );
  }
  const live = status.state === "live";
  return (
    <p className="flex items-center gap-2 text-xs leading-4 text-ink-3">
      <span
        aria-hidden
        className={
          live
            ? "size-2 bg-red-ink motion-safe:animate-pulse"
            : "size-2 border border-ink-3"
        }
      />
      <span
        className={
          live
            ? "font-mono text-[11px] font-bold tracking-[0.06em] text-red-ink uppercase"
            : "text-ink-2"
        }
      >
        {live ? "Live" : "Delayed"}
      </span>
      <span>
        checked{" "}
        <time dateTime={status.lastCheckedAt} className="font-mono">
          {formatClock(status.lastCheckedAt)} UTC
        </time>
      </span>
    </p>
  );
}
