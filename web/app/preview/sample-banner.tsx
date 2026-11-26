// The banner every sample-data preview carries, so invented values can never pass for real ones.
export function SampleBanner() {
  return (
    <div
      role="note"
      aria-label="Sample data notice"
      className="sticky top-0 z-20 border-b-2 border-red-ink bg-red-soft"
    >
      <p className="mx-auto max-w-[1240px] px-4 py-2 text-[13px] leading-[18px] text-ink sm:px-6 lg:px-10">
        <strong className="mr-2 font-mono text-[11px] font-bold tracking-[0.08em] text-red-ink uppercase">
          Sample data
        </strong>
        Every event and figure on this page is invented to show the design. None of it is real.
      </p>
    </div>
  );
}
