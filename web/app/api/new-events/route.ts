// How many events are newer than the one at the top of the reader's page, for the "N new
// events" bar. Ordering matches the feed: publication time, then id. The API's own count
// endpoint (spec: "a count of events newer than a given cursor") can replace this later.
import { listEvents } from "@/lib/api";

const MAX_COUNTED = 100;

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const id = Number(params.get("id"));
  const publishedAt = Date.parse(params.get("published_at") ?? "");
  if (!Number.isInteger(id) || Number.isNaN(publishedAt)) {
    return Response.json({ error: "id and published_at are required" }, { status: 400 });
  }

  let count = 0;
  try {
    const page = await listEvents("all", undefined, MAX_COUNTED);
    count = page.events.filter((event) => {
      const t = Date.parse(event.published_at);
      return t > publishedAt || (t === publishedAt && event.id > id);
    }).length;
  } catch {
    return Response.json({ error: "API unavailable" }, { status: 502 });
  }
  return Response.json(
    { count },
    { headers: { "Cache-Control": "no-store" } },
  );
}
