// Ingestion status (header) and source health (the Source status widget), from GET /v1/status.
// Styling hooks: data-status on the indicator, data-state on each source.
import { LocalTime } from "@/components/feed/local-time";
import {
  getStatus,
  type IngestionState,
  type IngestionStatus,
  type SourceState,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<IngestionState, string> = {
  starting: "Starting",
  live: "Live",
  degraded: "Some sources delayed",
  down: "Updates paused",
};

async function loadStatus(): Promise<IngestionStatus | null> {
  try {
    return await getStatus();
  } catch {
    return null;
  }
}

/** Live status indicator for the page header. */
export async function IngestionIndicator() {
  const current = await loadStatus();
  return <IngestionBadge status={current?.status ?? null} lastSuccessAt={current?.last_success_at ?? null} />;
}

export function IngestionBadge({
  status,
  lastSuccessAt,
  now,
}: {
  status: IngestionState | null;
  lastSuccessAt: string | null;
  now?: Date;
}) {
  const live = status === "live";
  return (
    <p
      role="status"
      data-status={status ?? "unknown"}
      className="flex items-center gap-2 text-xs leading-4 text-ink-3"
    >
      <span
        aria-hidden
        className={cn(
          "size-2 flex-none",
          live ? "bg-red-ink motion-safe:animate-pulse" : "border border-ink-3",
        )}
      />
      <span
        className={cn(
          live
            ? "font-mono text-[11px] font-bold tracking-[0.06em] text-red-ink uppercase"
            : "text-ink-2",
        )}
      >
        {status ? STATUS_LABEL[status] : "Status unavailable"}
      </span>
      {lastSuccessAt && (
        <span className="hidden sm:inline">
          checked <LocalTime iso={lastSuccessAt} style="short" now={now} className="font-mono" />
        </span>
      )}
    </p>
  );
}

/** Each source with its last successful check. */
export async function SourceStatus() {
  const current = await loadStatus();
  if (!current) {
    return (
      <p className="text-[13px] leading-[18px] text-ink-3">
        Source status could not be loaded.
      </p>
    );
  }
  return <SourceList status={current} />;
}

const DOT: Record<SourceState, string> = {
  ok: "bg-ink",
  stale: "bg-ink-3",
  failing: "bg-red-ink",
  pending: "border border-ink-3",
};

export function SourceList({ status, now }: { status: IngestionStatus; now?: Date }) {
  return (
    <ul aria-label="Sources" className="flex flex-col gap-1.5">
      {status.sources.map((source) => (
        <li
          key={source.id}
          data-state={source.state}
          className="grid grid-cols-[8px_minmax(0,1fr)_auto] items-center gap-x-2 text-[13px] leading-[18px]"
        >
          <span aria-hidden className={cn("size-1.5", DOT[source.state])} />
          <span className="truncate text-ink">{source.name}</span>
          <span className="font-mono text-[11px] text-ink-3">
            {source.state === "failing" && !source.last_success_at ? (
              <span className="text-red-ink">Failing</span>
            ) : source.state === "pending" || !source.last_success_at ? (
              "Not checked yet"
            ) : (
              <>
                {source.state === "failing" && <span className="text-red-ink">Failing · </span>}
                {source.state === "stale" && "Delayed · "}
                <span className="sr-only">Last checked </span>
                <LocalTime iso={source.last_success_at} style="short" now={now} />
              </>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}
