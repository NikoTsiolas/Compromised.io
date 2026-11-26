// The event page while it loads: the same column, line heights and picture box as the page, in
// the homepage skeleton's breathing bars, so nothing jumps when the content arrives.
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function Bar({ className }: { className?: string }) {
  return <Skeleton className={cn("skm-bar rounded-[2px]", className)} />;
}

export function EventSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading the event" className="max-w-[720px]">
      <Bar className="mb-2 h-3.5 w-40" />
      <Bar className="h-7 w-full sm:h-8" />
      <Bar className="mt-1.5 h-7 w-2/3 sm:h-8" />
      <Bar className="mt-3 h-3 w-56" />
      <Bar className="mt-5 aspect-[16/10] w-full" />
      <Bar className="mt-5 h-4 w-full" />
      <Bar className="mt-2 h-4 w-5/6" />
    </div>
  );
}
