// Event page addresses are settled here, before the page starts streaming, because a streamed
// page has already sent its status (200) by the time it could find out the event is missing:
// - an unknown id, or something that is not an id, gets the event not-found page with a 404;
// - the id of an event deleted by regrouping gets a permanent redirect to the event its story
//   joined, so an old shared link keeps working.
// The check asks the API for the status only. If the API cannot be reached the page renders and
// says so itself.
import { NextResponse, type NextRequest } from "next/server";

import { lookUpEvent } from "@/lib/api";
import { eventPath } from "@/lib/event";

export const config = { matcher: "/events/:id" };

export async function proxy(request: NextRequest) {
  const id = request.nextUrl.pathname.split("/")[2] ?? "";
  const found = await lookUpEvent(id);
  if (found.kind === "moved") {
    return NextResponse.redirect(new URL(eventPath(found.id), request.url), 308);
  }
  if (found.kind === "missing") {
    return NextResponse.rewrite(new URL("/events/unknown", request.url));
  }
  return NextResponse.next();
}
