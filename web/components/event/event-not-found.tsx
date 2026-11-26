// Shown for an event address that leads nowhere: an id that never existed, or not an id at all.
// Set in the "How we score" page's column and type; no design of its own.
import Link from "next/link";

export function EventNotFound() {
  return (
    <>
      <h1 className="text-[26px] leading-[30px] font-bold tracking-[-0.02em] text-ink sm:text-[32px] sm:leading-[36px]">
        Event not found
      </h1>
      <p className="mt-4 max-w-[68ch] text-[15px] leading-[22px] text-ink-2">
        There is no event at this address. It may have been mistyped, or the link may be
        incomplete.
      </p>
      <p className="mt-4 text-[15px] leading-[22px]">
        <Link
          href="/"
          className="font-medium text-ink underline decoration-1 underline-offset-4"
        >
          Back to the feed
        </Link>
      </p>
    </>
  );
}
