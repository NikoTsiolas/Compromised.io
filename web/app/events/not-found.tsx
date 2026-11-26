// The not-found page for event addresses: an unknown id (sent here by Proxy with a 404), or an
// event that disappeared between Proxy's check and the page's own request.
import { EventNotFound } from "@/components/event/event-not-found";
import { SiteHeader } from "@/components/site/site-header";

export default function NotFound() {
  return (
    <>
      {/* React places this in <head>; route metadata is not applied to a not-found render. */}
      <title>Event not found · Compromised</title>
      <SiteHeader />
      <main className="mx-auto max-w-[1240px] px-4 pt-8 pb-16 sm:px-6 sm:pt-10 lg:px-10">
        <EventNotFound />
      </main>
    </>
  );
}
