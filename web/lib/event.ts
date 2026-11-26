// One event's page (#11): its address and the plain text that describes it to search engines and
// link previews. Everything here is built from text the API stores and sends as plain text.
import type { EventDetail } from "@/lib/api";

/**
 * An event's page address. The id is the API's event id, which never changes as sources join the
 * event; an event deleted by regrouping redirects to the event its story joined.
 */
export function eventPath(id: string | number): string {
  return `/events/${id}`;
}

/** Only real event ids have pages; the sample preview's made-up ids do not. */
export function hasEventPage(id: string): boolean {
  return /^\d+$/.test(id);
}

const DESCRIPTION_LIMIT = 200;

/**
 * The page's description: the AI summary when there is one, else the earliest publisher's own
 * excerpt, else the trust label and who reported it. Whitespace collapsed, cut at a word.
 */
export function describeEvent(event: EventDetail): string {
  const excerpt = event.sources.find((s) => s.excerpt.trim())?.excerpt;
  const publishers = [...new Set(event.sources.map((s) => s.publisher))].join(", ");
  const text =
    event.summary ||
    excerpt ||
    [event.trust?.label, publishers && `Sources: ${publishers}`].filter(Boolean).join(". ") ||
    event.title;
  return clip(text.replace(/\s+/g, " ").trim(), DESCRIPTION_LIMIT);
}

function clip(text: string, limit: number): string {
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit - 1);
  const atWord = cut.slice(0, cut.lastIndexOf(" "));
  return `${(atWord.length > limit / 2 ? atWord : cut).replace(/[\s,;:.]+$/, "")}…`;
}
