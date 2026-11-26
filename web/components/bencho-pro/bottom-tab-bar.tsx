"use client";

// The phone and tablet tab bar (Option C, after Bluesky's bottom bar on Mobbin): Featured, Feed,
// Search, Watching and Charts. Adapted from the Bencho "Tab bar" block (tab-bar, Bencho Pro
// licence, see README.md). Kept from the block: icons until chosen, the chosen item opening to
// show its name in a grid column that eases 0fr -> 1fr, and one light tile that chases the chosen
// item's live box on a spring (bounce 50), snapping under reduced motion; softened-square bar and
// concentric tile. Changed: these are links to places with their own URLs, so it is a <nav>
// with aria-current instead of a tablist, and every item keeps its name for screen readers;
// colours mapped to our tokens; the bar floats above the page's safe area, and the page reserves
// its height so it never covers the last post.
import { BarChart3, Eye, House, Rss, Search, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useLayoutEffect, useRef } from "react";

import "./bottom-tab-bar.css";

export type TabBarItem = "featured" | "feed" | "search" | "watching" | "charts";

const ITEMS: { id: TabBarItem; label: string; href: string; Icon: LucideIcon }[] = [
  { id: "featured", label: "Featured", href: "/", Icon: House },
  { id: "feed", label: "Feed", href: "/feed", Icon: Rss },
  { id: "search", label: "Search", href: "/search", Icon: Search },
  { id: "watching", label: "Watching", href: "/feed?watching=1", Icon: Eye },
  { id: "charts", label: "Charts", href: "/feed?view=charts", Icon: BarChart3 },
];

const BOUNCE = 50;

export function BottomTabBar({ current }: { current: TabBarItem }) {
  const items = useRef<(HTMLAnchorElement | null)[]>([]);
  const tile = useRef<HTMLSpanElement | null>(null);
  const pos = useRef({ x: 0, w: 0, vx: 0, vw: 0 });
  const on = ITEMS.findIndex((i) => i.id === current);
  const zeta = 1 - BOUNCE * 0.0055;

  // First paint: the tile is simply where the chosen item is.
  useLayoutEffect(() => {
    const t = items.current[on];
    if (!t || !tile.current) return;
    pos.current = { x: t.offsetLeft, w: t.offsetWidth, vx: 0, vw: 0 };
    tile.current.style.transform = `translateX(${t.offsetLeft}px)`;
    tile.current.style.width = `${t.offsetWidth}px`;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // After a change (and while the chosen item widens to show its name): chase its live box.
  useEffect(() => {
    const el = tile.current;
    if (!el) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      const t = items.current[on];
      if (t) {
        el.style.transform = `translateX(${t.offsetLeft}px)`;
        el.style.width = `${t.offsetWidth}px`;
      }
      return;
    }
    const k = 260;
    const c = 2 * Math.sqrt(k) * zeta;
    let raf = 0;
    let last = 0;
    let quiet = 0;
    const step = (now: number) => {
      const t = items.current[on];
      if (!t) return;
      const dt = last ? Math.min(0.032, (now - last) / 1000) : 1 / 60;
      last = now;
      const p = pos.current;
      const tx = t.offsetLeft;
      const tw = t.offsetWidth;
      p.vx += (k * (tx - p.x) - c * p.vx) * dt;
      p.vw += (k * (tw - p.w) - c * p.vw) * dt;
      p.x += p.vx * dt;
      p.w += p.vw * dt;
      el.style.transform = `translateX(${p.x.toFixed(2)}px)`;
      el.style.width = `${p.w.toFixed(2)}px`;
      const still =
        Math.abs(tx - p.x) < 0.2 && Math.abs(tw - p.w) < 0.2 && Math.abs(p.vx) < 2 && Math.abs(p.vw) < 2;
      quiet = still ? quiet + 1 : 0;
      if (quiet < 6) raf = requestAnimationFrame(step);
      else {
        el.style.transform = `translateX(${tx}px)`;
        el.style.width = `${tw}px`;
        Object.assign(p, { x: tx, w: tw, vx: 0, vw: 0 });
      }
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [on, zeta]);

  return (
    <nav aria-label="Tab bar" className="tbb-dock">
      <div className="tbb">
        <span ref={tile} className="tbb-tile" aria-hidden="true" />
        {ITEMS.map(({ id, label, href, Icon }, i) => (
          <Link
            key={id}
            ref={(el) => {
              items.current[i] = el;
            }}
            href={href}
            aria-label={label}
            aria-current={i === on ? "page" : undefined}
            data-on={i === on || undefined}
            className="tbb-tab"
          >
            <Icon className="tbb-icon" size={18} strokeWidth={2} aria-hidden="true" />
            <span className="tbb-name" aria-hidden="true">
              <span>{label}</span>
            </span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
