// The homepage while it loads: the same grid, boxes and line heights as the real page
// (the lead story and its picture, three cards, the widget rail, feed rows), so when the
// content arrives nothing jumps. On shadcn Skeleton.
//
// The bars breathe in colour, not opacity, after the Bencho "Skeleton morph" block (Bencho Pro
// licence, see README.md): "the breath is in the COLOUR, not the opacity, so it can keep going
// on a bar still waiting its turn". Its morph into the content is not used here, because the
// content is streamed in by the server rather than hidden inside the skeleton; the reveal is a
// short view transition instead (app/page.tsx). Breathing stops under reduced motion.
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function Bar({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <Skeleton className={cn("skm-bar rounded-[2px]", className)} style={style} />;
}

export function HomeSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading events">
      <div className="h-11 border-b border-rule" />
      <div className="home-grid">
        <div className="home-featured min-w-0 pt-6 sm:pt-8">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] md:gap-8">
            <Bar className="aspect-[16/10] w-full md:order-2" />
            <div className="flex flex-col gap-3 md:order-1">
              <Bar className="h-3 w-1/3" />
              <Bar className="h-7 w-full" />
              <Bar className="h-7 w-4/5" />
              <Bar className="h-7 w-3/5" />
              <Bar className="mt-2 h-3 w-1/2" />
              <Bar className="mt-3 h-4 w-full" />
              <Bar className="h-4 w-5/6" />
            </div>
          </div>
          <div className="mt-6 grid grid-cols-1 gap-y-4 border-t border-rule pt-5 sm:mt-8 sm:grid-cols-3 sm:gap-x-5 sm:pt-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="grid grid-cols-[minmax(0,1fr)_96px] gap-x-4 sm:flex sm:flex-col sm:gap-3">
                <Bar className="col-start-2 aspect-[16/10] w-full sm:order-first" />
                <div className="col-start-1 row-start-1 flex flex-col gap-2">
                  <Bar className="h-3 w-2/5" />
                  <Bar className="h-4 w-full" />
                  <Bar className="h-4 w-4/5" />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="home-rail flex flex-col gap-4">
          {[160, 120, 140].map((h, i) => (
            <Bar key={i} className="w-full" style={{ height: h }} />
          ))}
        </div>
        <div className="home-feed min-w-0">
          <div className="mt-8 h-6 border-b border-rule-strong" />
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="grid grid-cols-[minmax(0,1fr)_96px] gap-x-4 border-b border-rule py-4 sm:grid-cols-[200px_minmax(0,1fr)] sm:gap-x-6 sm:py-5"
            >
              <Bar className="col-start-2 aspect-[4/3] w-full sm:col-start-1" />
              <div className="col-start-1 row-start-1 flex flex-col gap-2 sm:col-start-2">
                <Bar className="h-3 w-1/4" />
                <Bar className="h-5 w-4/5" />
                <Bar className="h-3 w-1/5" />
                <Bar className="mt-2 h-4 w-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
