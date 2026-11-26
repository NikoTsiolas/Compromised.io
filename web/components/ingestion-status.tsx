// Ingestion status and source health. Deliberately unstyled: design is #9. Restyle by the
// data-status / data-state attributes; the wording lives in the two label maps below.
import {
  getStatus,
  type IngestionState,
  type IngestionStatus,
  type SourceState,
} from "@/lib/api";
import { formatOriginal, formatRelative } from "@/lib/time";

const STATUS_LABEL: Record<IngestionState, string> = {
  starting: "Starting",
  live: "Live",
  degraded: "Some sources delayed",
  down: "Updates paused",
};

const STATE_LABEL: Record<SourceState, string> = {
  pending: "Not checked yet",
  ok: "Last checked",
  failing: "Failing; last checked",
  stale: "Delayed; last checked",
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
  const status = current?.status;
  return (
    <p role="status" data-status={status ?? "unknown"}>
      {status ? STATUS_LABEL[status] : "Status unavailable"}
    </p>
  );
}

/** Each source with its last successful check. */
export async function SourceHealthList() {
  const current = await loadStatus();
  if (!current) {
    return <p>Source status could not be loaded.</p>;
  }
  return (
    <ul aria-label="Sources">
      {current.sources.map((source) => (
        <li key={source.id} data-state={source.state}>
          {source.name}
          {": "}
          {source.last_success_at ? (
            <>
              {STATE_LABEL[source.state]}{" "}
              <time dateTime={source.last_success_at}>
                {formatOriginal(source.last_success_at)}
              </time>
              {" ("}
              {formatRelative(source.last_success_at)}
              {")"}
            </>
          ) : source.state === "pending" ? (
            STATE_LABEL.pending
          ) : (
            "Not checked successfully yet"
          )}
        </li>
      ))}
    </ul>
  );
}
