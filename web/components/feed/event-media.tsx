"use client";

// An event's picture. The publisher's own feed image when there is one: loaded by the reader's
// browser straight from the publisher, with no referrer, never through our server, and credited
// to the publisher on the image. If it fails to load (before or after hydration) the designed
// tile takes its place, and the credit goes with it.
import { useEffect, useRef, useState } from "react";

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
  const img = useRef<HTMLImageElement>(null);

  // An image that failed before React attached its handlers never fires onError again.
  useEffect(() => {
    const el = img.current;
    if (el && el.complete && el.naturalWidth === 0) setFailed(true);
  }, []);

  const showImage = Boolean(image) && !failed;
  return (
    <AspectRatio
      ratio={ratio}
      className={cn("overflow-hidden rounded-[2px] bg-surface", className)}
    >
      {showImage ? (
        <>
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
            className="absolute inset-0 size-full object-cover"
          />
          <span
            className={cn(
              "absolute right-1.5 bottom-1.5 max-w-[80%] truncate rounded-[2px] bg-[#111111]/70 px-1.5 py-0.5 font-mono leading-4 text-[#f6f5f1]",
              size === "thumb" ? "text-[9px]" : "text-[10px]",
            )}
          >
            Image: {image!.publisher}
          </span>
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
}
