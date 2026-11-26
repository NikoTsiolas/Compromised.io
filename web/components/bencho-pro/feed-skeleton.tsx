// The Feed while it loads: post-shaped skeletons laid to the same lines as a post (avatar, the
// company line, headline, summary, the 16:9 picture, trust and actions), so nothing jumps when
// the posts arrive. After the Bencho "Load cards" block (load-cards, Bencho Pro licence, see
// README.md): each skeleton eases in out of a blur, a few pixels low, one after another, and a
// soft light runs across its bars while it waits. Its "develop" (the content blurring into
// focus inside the card) is not used, because the server streams the posts in; the page's
// Suspense reveal is a short view transition instead. Still under reduced motion.
import "./feed-skeleton.css";

function Bar({ w, h = 12, className = "" }: { w: string; h?: number; className?: string }) {
  return <i className={`lcd-bar ${className}`} style={{ width: w, height: h }} />;
}

export function FeedSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading posts" className="feed-page">
      <div className="feed-grid">
        <div className="feed-nav hidden md:block">
          <div className="flex flex-col gap-3 pt-6">
            {[40, 72, 84, 88, 80, 64, 64].map((w, i) => (
              <Bar key={i} w={`${w}px`} h={14} className="ml-3" />
            ))}
          </div>
        </div>
        <div className="feed-main min-w-0">
          <div className="h-11 border-b border-rule" />
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="lcd-card flex gap-3 border-b border-rule px-4 pt-4 pb-3 sm:px-5"
              style={{ animationDelay: `${60 + i * 90}ms` }}
            >
              <i className="lcd-bar size-10 flex-none rounded-full!" />
              <div className="flex min-w-0 flex-1 flex-col gap-3">
                <Bar w="45%" h={14} />
                <Bar w="92%" h={16} />
                <Bar w="80%" />
                <i className="lcd-bar aspect-video w-full rounded-[12px]!" />
                <Bar w="60%" />
                <Bar w="70%" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
