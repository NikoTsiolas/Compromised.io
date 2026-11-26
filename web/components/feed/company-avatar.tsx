// The affected company as a post's avatar (Option A): its logo from Simple Icons when the
// catalog resolves one, otherwise its lettermark, on the same tinted ground its picture tile
// uses (so one company always looks the same). With no named organisation, a quiet dashed
// circle: the post is still from somewhere, but we do not know whom. Decorative: the company's
// name is always written beside it.
import { lettermark, tintFor } from "@/components/feed/event-tile";
import type { Logo } from "@/lib/feed";
import { cn } from "@/lib/utils";

export function CompanyAvatar({
  organization,
  logo,
  className,
}: {
  organization: string | null | undefined;
  logo: Logo | null | undefined;
  className?: string;
}) {
  if (!organization) {
    return (
      <span
        aria-hidden
        data-avatar="unknown"
        className={cn(
          "block size-10 flex-none rounded-full border border-dashed border-ink-3/60",
          className,
        )}
      />
    );
  }
  return (
    <span
      aria-hidden
      data-avatar={logo ? "logo" : "lettermark"}
      data-tile={tintFor(organization)}
      className={cn(
        "event-tile grid size-10 flex-none place-items-center overflow-hidden rounded-full",
        className,
      )}
    >
      {logo ? (
        <svg viewBox="0 0 24 24" className="size-[18px] fill-current text-ink">
          <path d={logo.path} />
        </svg>
      ) : (
        <span className="text-[15px] leading-5 font-bold text-ink">
          {lettermark(organization)}
        </span>
      )}
    </span>
  );
}
