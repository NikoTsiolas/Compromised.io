// The two top-level destinations (#16): Featured, the first page, and the Feed. Plain links with
// aria-current, styled as the site's underline tabs so they read as a pair; shown on every width
// (beside the wordmark from 640px, on a row of their own beneath it on phones).
import Link from "next/link";

import { cn } from "@/lib/utils";

export type Destination = "featured" | "feed";

const DESTINATIONS: { id: Destination; label: string; href: string }[] = [
  { id: "featured", label: "Featured", href: "/" },
  { id: "feed", label: "Feed", href: "/feed" },
];

export function PrimaryNav({
  current,
  className,
}: {
  current?: Destination;
  className?: string;
}) {
  return (
    <nav aria-label="Primary" className={className}>
      <ul className="flex items-stretch gap-5">
        {DESTINATIONS.map((d) => {
          const on = d.id === current;
          return (
            <li key={d.id} className="flex">
              <Link
                href={d.href}
                aria-current={on ? "page" : undefined}
                className={cn(
                  "relative inline-flex min-h-11 items-center text-[15px] leading-5 font-medium text-ink-3 hover:text-ink",
                  "after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-ink after:opacity-0 after:transition-opacity after:duration-(--motion-base)",
                  on && "font-bold text-ink after:opacity-100",
                )}
              >
                {d.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
