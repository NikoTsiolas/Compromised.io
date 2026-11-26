// Where Proxy (proxy.ts) sends an event address that leads nowhere. It calls notFound() while
// the build prerenders it, so it is stored, and served, with a real HTTP 404 and the events
// not-found page (app/events/not-found.tsx). A rewrite's own status would be overwritten by the
// page's 200.
import { notFound } from "next/navigation";

export default function UnknownEvent() {
  notFound();
}
