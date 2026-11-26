// Odometer digits, after the Bencho rolling-counter block (MIT): each digit is a strip of 0-9
// behind a window with masked edges, moved to its digit. Only the digit-strip technique is kept
// (no buttons, drag or fling); a CSS transition replaces its per-column spring. Monospace,
// tabular. Off under prefers-reduced-motion via the global rule.
export function RollingNumber({ value }: { value: number }) {
  const digits = String(Math.max(0, Math.trunc(value))).split("");
  return (
    <span className="inline-flex h-[1.25em] overflow-hidden font-mono tabular [mask-image:linear-gradient(transparent,#000_20%,#000_80%,transparent)]">
      <span className="sr-only">{value}</span>
      {digits.map((d, i) => (
        <span key={digits.length - i} aria-hidden className="w-[1ch] overflow-hidden">
          <span
            className="flex flex-col transition-transform duration-[420ms] ease-[cubic-bezier(0.3,1.2,0.4,1)]"
            style={{ transform: `translateY(${-Number(d) * 1.25}em)` }}
          >
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
              <span key={n} className="h-[1.25em] leading-[1.25em]">
                {n}
              </span>
            ))}
          </span>
        </span>
      ))}
    </span>
  );
}
