// The designed tile an event shows when it has no usable publisher image, which is most events.
// It must look intentional: one mark, centred, on a restrained tinted ground with a hairline.
// The mark is the affected company's logo from Simple Icons when the catalog can resolve it,
// otherwise a lettermark; with no organisation at all, the category's name. The tint is picked
// from five muted grounds by the organisation's name, so one company always gets the same one.
import type { Logo } from "@/lib/feed";
import { cn } from "@/lib/utils";

const TINTS = 5;

export function tintFor(name: string): number {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.codePointAt(0)!) >>> 0;
  return (h % TINTS) + 1;
}

/** "1Password" -> "1", "AT&T" -> "A", "Windows" -> "W". */
export function lettermark(name: string): string {
  const ch = [...name.trim()].find((c) => /[\p{L}\p{N}]/u.test(c));
  return (ch ?? "?").toUpperCase();
}

export function EventTile({
  organization,
  logo,
  fallbackLabel,
  size,
  className,
}: {
  organization: string | null | undefined;
  logo: Logo | null | undefined;
  /** Shown when there is no organisation: the category's plain-language name. */
  fallbackLabel: string;
  size: "lead" | "card" | "thumb" | "post";
  className?: string;
}) {
  const key = organization ?? fallbackLabel;
  const kind = logo ? "logo" : organization ? "lettermark" : "category";
  const caption = size !== "thumb" && kind !== "category" ? organization : null;
  return (
    <div
      data-tile={tintFor(key)}
      className={cn(
        "event-tile absolute inset-0 flex flex-col items-center justify-center gap-[3cqmin] overflow-hidden [container-type:size]",
        className,
      )}
    >
      {kind === "logo" ? (
        <div data-media="logo" className="grid place-items-center">
          <svg
            role="img"
            aria-label={`${logo!.title} logo`}
            viewBox="0 0 24 24"
            className={cn(
              "fill-current text-ink",
              size === "thumb" ? "size-[38cqmin]" : size === "post" ? "size-[18cqmin]" : "size-[26cqmin]",
            )}
          >
            <path d={logo!.path} />
          </svg>
        </div>
      ) : kind === "lettermark" ? (
        <div
          data-media="lettermark"
          aria-hidden
          className={cn(
            "leading-none font-bold tracking-[-0.04em] text-ink",
            size === "thumb" ? "text-[36cqmin]" : size === "post" ? "text-[20cqmin]" : "text-[30cqmin]",
          )}
        >
          {lettermark(organization!)}
        </div>
      ) : (
        <div
          data-media="category"
          aria-hidden
          className="px-3 text-center font-mono text-[11px] tracking-[0.08em] text-ink-2 uppercase"
        >
          {fallbackLabel}
        </div>
      )}
      {caption && (
        <div
          aria-hidden
          className={cn(
            "max-w-[80%] truncate text-center font-bold tracking-[-0.01em] text-ink-2 @max-[160px]:hidden",
            size === "lead" || size === "post" ? "text-[15px]" : "text-[12px]",
          )}
        >
          {caption}
        </div>
      )}
    </div>
  );
}
