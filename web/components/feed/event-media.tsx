"use client";

// An event's picture. The publisher's own feed image when there is one: loaded by the reader's
// browser straight from the publisher, with no referrer, never through our server, and credited
// to the publisher on the image. If it fails to load (before or after hydration) the designed
// tile takes its place, and the credit goes with it. The box is reserved by its aspect ratio
// before anything loads; while the picture is on its way a quiet shimmer (Bencho "Image
// shimmer", Pro) fills it, and the picture fades in over it, so nothing around it moves.
import { useEffect, useRef, useState } from "react";

import "@/components/bencho-pro/image-shimmer.css";
import { EventTile } from "@/components/feed/event-tile";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import type { Logo, PublisherImage } from "@/lib/feed";
import { cn } from "@/lib/utils";

export function EventMedia({
  image,
  logo,
  organization,
  fallbackLabel,
  size,
  ratio = 16 / 10,
  priority = false,
  className,
}: {
  image: PublisherImage | null | undefined;
  logo: Logo | null | undefined;
  organization: string | null | undefined;
  fallbackLabel: string;
  size: "lead" | "card" | "thumb";
  ratio?: number;
  /** The lead image loads eagerly; every other image lazily. */
  priority?: boolean;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const img = useRef<HTMLImageElement>(null);

  // An image that failed before React attached its handlers never fires onError again.
  useEffect(() => {
    const el = img.current;
    if (!el || !el.complete) return;
    // Settled before hydration: reflect it (a sync with the DOM, not a cascade).
     
    if (el.naturalWidth === 0) setFailed(true);
    else setLoaded(true);
  }, []);

  const showImage = Boolean(image) && !failed;
  const picture = (
    <AspectRatio
      ratio={ratio}
      className={cn("overflow-hidden rounded-[2px] bg-surface", className)}
    >
      {showImage ? (
        <>
          {!loaded && <div aria-hidden className="ish-tile absolute inset-0" />}
          {/* A plain <img>, not next/image: the optimiser would fetch the picture through our
              server, which the image rule forbids. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            ref={img}
            src={image!.url}
            alt={`Picture from ${image!.publisher}`}
            referrerPolicy="no-referrer"
            crossOrigin={undefined}
            loading={priority ? "eager" : "lazy"}
            decoding="async"
            onError={() => setFailed(true)}
            onLoad={() => setLoaded(true)}
            data-loaded={loaded || undefined}
            className="event-img absolute inset-0 size-full object-cover"
          />
          {size !== "thumb" && (
            <span
              className={cn(
                size === "card" && "hidden sm:block",
                "absolute right-1.5 bottom-1.5 max-w-[80%] truncate rounded-[2px] bg-[#111111]/75 px-1.5 py-0.5 font-mono text-[10px] leading-4 text-[#f6f5f1] transition-opacity duration-(--motion-base)",
                loaded ? "opacity-100" : "opacity-0",
              )}
            >
              Image: {image!.publisher}
            </span>
          )}
        </>
      ) : (
        <EventTile
          organization={organization}
          logo={logo}
          fallbackLabel={fallbackLabel}
          size={size}
        />
      )}
    </AspectRatio>
  );
  if (size === "lead") return picture;
  // Small pictures (feed rows always, cards on phones) carry their credit on a line of its own
  // beneath them, always reserved, so the row is the same height whether the picture loads,
  // fails or never existed.
  return (
    <div>
      {picture}
      <p
        className={cn(
          "mt-1 h-3.5 truncate font-mono text-[10px] leading-3.5 text-ink-3",
          size === "card" && "sm:hidden",
        )}
      >
        {showImage && loaded ? `Image: ${image!.publisher}` : ""}
      </p>
    </div>
  );
}
