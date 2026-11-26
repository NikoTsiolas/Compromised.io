// Loading state for the feed: the shape of tabs and rows on shadcn Skeleton, no spinner.
import { Skeleton } from "@/components/ui/skeleton";

export function FeedSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading events">
      <div className="flex h-11 items-center gap-6">
        {[28, 64, 80, 84, 76, 64, 64].map((w, i) => (
          <Skeleton key={i} className="h-3.5 bg-rule" style={{ width: w }} />
        ))}
      </div>
      <div className="h-0.5 bg-rule-strong" />
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="grid gap-2 border-b border-rule py-4 sm:grid-cols-[72px_minmax(0,1fr)] sm:gap-x-6 lg:grid-cols-[88px_minmax(0,1fr)_176px]"
        >
          <Skeleton className="h-3 w-12 bg-rule" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-4/5 bg-rule" />
            <Skeleton className="h-4 w-3/5 bg-rule" />
          </div>
        </div>
      ))}
    </div>
  );
}
