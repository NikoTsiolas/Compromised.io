// Wordmark, option 3 of the design notes: "Compromised" in Helvetica Neue Bold, title case, with
// the tagline beneath in small capitals, both lines on one left edge like an FT masthead and
// folio. Type only; no logo, no shield.
import Link from "next/link";

export function Wordmark() {
  return (
    <Link
      href="/"
      aria-label="Compromised, home"
      className="group inline-flex flex-col gap-1 leading-none"
    >
      <span className="text-[22px] leading-[22px] font-bold tracking-[-0.02em] text-ink sm:text-[26px] sm:leading-[26px]">
        Compromised
      </span>
      <span className="text-[10px] leading-3 font-medium tracking-[0.08em] text-ink-3 uppercase sm:text-[11px]">
        Know what&rsquo;s been compromised
      </span>
    </Link>
  );
}
