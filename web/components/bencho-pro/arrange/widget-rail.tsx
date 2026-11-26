"use client";

// The widget rail beside the feed: the reader drags a widget by its handle to reorder the rail,
// moves it with the keyboard, and switches the rail between the left and right side. The
// arrangement is kept in local storage (arrangement.ts). On phones and tablets the widgets
// stack below the featured stories and are not draggable.
//
// Adapted from the Bencho "Reorder list" block (Arrange), Bencho Pro licence, see ../README.md.
// Kept from the block: the pointer drag with pointer capture (wrapped, because capture throws
// for a pointer that is not live), the held item pinned to where the finger STARTED rather than
// to the slot it currently occupies, the list reordering underneath the gesture as soon as the
// held item's own position says it belongs elsewhere, and the elastic spring the others ride
// to their new places. Changed: rows are cards of different heights, so slots are read from the
// layout instead of a fixed pitch; the liquid "goo" filter, velocity squash and lean are gone
// (decorative, and the filter must never touch text); a handle replaces whole-row dragging so
// the widgets' own controls still work; and arrow keys, Home and End move a widget for readers
// who do not use a pointer, with the result announced.
import { animate, motion, useMotionValue, useReducedMotion } from "framer-motion";
import { ArrowLeftRight, GripVertical } from "lucide-react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { flushSync } from "react-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import {
  apply,
  load,
  normalise,
  prePaintScript,
  save,
  type Arrangement,
  type RailSide,
} from "./arrangement";

export type RailWidget = {
  id: string;
  title: string;
  description?: string;
  body: ReactNode;
};

/* The block's elastic, damped a little further (block: damping 14, ~6% overshoot), because a
   card the size of a widget overshooting its slot reads as a wobble on a news page. */
const LIQUID = { type: "spring" as const, stiffness: 220, damping: 20, mass: 0.5 };

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export function WidgetRail({
  widgets,
  sideSwitch = true,
}: {
  widgets: RailWidget[];
  /** Off on the Feed, whose left column is the navigation (#16). */
  sideSwitch?: boolean;
}) {
  const ids = widgets.map((w) => w.id);
  const byId = new Map(widgets.map((w) => [w.id, w]));
  const still = useReducedMotion();

  // The first render matches the server (default order); the stored one arrives after mount.
  const [arrangement, setArrangement] = useState<Arrangement>(() => normalise(null, ids));
  const [held, setHeld] = useState<string | null>(null);
  // True once the stored arrangement is read and the handlers are live (data-ready).
  const [ready, setReady] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const refocus = useRef<string | null>(null);
  const items = useRef(new Map<string, HTMLLIElement>());
  const grips = useRef(new Map<string, HTMLButtonElement>());
  const grab = useRef<{ id: string; startY: number; startTop: number; dy: number } | null>(null);
  const heldY = useMotionValue(0);

  const idKey = ids.join("|");
  useEffect(() => {
    const stored = load(idKey.split("|"));
    apply(stored);
    // Reading the reader's stored arrangement is a sync with an external system (storage).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setArrangement(stored);
    setReady(true);
  }, [idKey]);

  const commit = useCallback((next: Arrangement) => {
    apply(next);
    save(next);
    setArrangement(next);
  }, []);

  // Pinned to where the drag started, re-read after every reorder (the block's "THE fix for
  // the jump"), and focus kept on a handle the keyboard just moved.
  useLayoutEffect(() => {
    const g = grab.current;
    if (g) {
      const el = items.current.get(g.id);
      if (el) heldY.set(g.startTop + g.dy - el.offsetTop);
    }
    if (refocus.current) {
      grips.current.get(refocus.current)?.focus();
      refocus.current = null;
    }
  }, [arrangement, heldY]);

  const moveTo = (id: string, index: number, announce: boolean) => {
    const order = arrangement.order.filter((x) => x !== id);
    const at = clamp(index, 0, order.length);
    order.splice(at, 0, id);
    if (order.join() === arrangement.order.join()) return;
    commit({ ...arrangement, order });
    if (announce) {
      setAnnouncement(
        `${byId.get(id)?.title} moved to position ${at + 1} of ${order.length}`,
      );
    }
  };

  const onKey = (id: string) => (e: React.KeyboardEvent) => {
    const at = arrangement.order.indexOf(id);
    const last = arrangement.order.length - 1;
    const to =
      e.key === "ArrowUp" ? at - 1
      : e.key === "ArrowDown" ? at + 1
      : e.key === "Home" ? 0
      : e.key === "End" ? last
      : null;
    if (to === null) return;
    e.preventDefault();
    refocus.current = id;
    moveTo(id, to, true);
  };

  const down = (id: string) => (e: React.PointerEvent) => {
    if (grab.current || e.button !== 0) return;
    const el = items.current.get(id);
    if (!el) return;
    try {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    } catch {
      /* not a live pointer; the drag works without capture */
    }
    grab.current = { id, startY: e.clientY, startTop: el.offsetTop, dy: 0 };
    heldY.set(0);
    setHeld(id);
  };

  const move = (e: React.PointerEvent) => {
    const g = grab.current;
    if (!g) return;
    const el = items.current.get(g.id);
    if (!el) return;
    g.dy = e.clientY - g.startY;
    const top = g.startTop + g.dy;
    heldY.set(top - el.offsetTop);
    // Where the held card's own middle says it belongs, among the others' middles.
    const middle = top + el.offsetHeight / 2;
    const others = arrangement.order.filter((x) => x !== g.id);
    let want = 0;
    for (const other of others) {
      const o = items.current.get(other);
      if (o && o.offsetTop + o.offsetHeight / 2 < middle) want++;
    }
    if (want !== arrangement.order.indexOf(g.id)) moveTo(g.id, want, false);
  };

  const up = () => {
    const g = grab.current;
    if (!g) return;
    grab.current = null;
    const title = byId.get(g.id)?.title;
    const at = arrangement.order.indexOf(g.id);
    setAnnouncement(`${title} moved to position ${at + 1} of ${arrangement.order.length}`);
    if (still) {
      heldY.set(0);
      setHeld(null);
    } else {
      animate(heldY, 0, LIQUID).then(() => setHeld(null));
    }
  };

  const otherSide: RailSide = arrangement.side === "right" ? "left" : "right";

  // The rail and the stories glide to their new sides as a view transition where the browser
  // supports one (names are set only for its duration, see .rail-switching in globals.css).
  const switchSide = () => {
    const next = { ...arrangement, side: otherSide };
    const run = () => flushSync(() => commit(next));
    const doc = document as Document & {
      startViewTransition?: (update: () => void) => { finished: Promise<void> };
    };
    if (still || !doc.startViewTransition) {
      run();
      return;
    }
    const root = document.documentElement;
    root.classList.add("rail-switching");
    doc
      .startViewTransition(run)
      .finished.finally(() => root.classList.remove("rail-switching"));
  };

  return (
    <aside aria-label="Widgets" data-ready={ready || undefined} className="home-rail min-w-0">
      <script
        // Applies a stored arrangement before first paint; see arrangement.ts.
        dangerouslySetInnerHTML={{ __html: prePaintScript(ids) }}
      />
      <div className="mb-3 hidden items-center justify-between lg:flex">
        <p className="font-mono text-[11px] leading-4 tracking-[0.06em] text-ink-3 uppercase">
          At a glance
        </p>
        {sideSwitch && (
        <button
          type="button"
          onClick={switchSide}
          className="inline-flex h-7 cursor-pointer items-center gap-1.5 rounded-[2px] px-1.5 text-xs text-ink-3 hover:bg-surface hover:text-ink"
        >
          <ArrowLeftRight aria-hidden className="size-3.5" strokeWidth={1.75} />
          Move widgets to the {otherSide}
        </button>
        )}
      </div>
      <ul className="relative flex flex-col gap-4">
        {arrangement.order.map((id) => {
          const widget = byId.get(id)!;
          const isHeld = held === id;
          const titleId = `widget-${id}-title`;
          return (
            <motion.li
              key={id}
              ref={(el: HTMLLIElement | null) => {
                if (el) items.current.set(id, el);
                else items.current.delete(id);
              }}
              layout={still || isHeld ? false : "position"}
              transition={LIQUID}
              data-held={isHeld || undefined}
              style={{
                order: `var(--widget-${id}, 0)`,
                ...(isHeld ? { y: heldY, zIndex: 2, position: "relative" } : {}),
              }}
            >
              <Card
                role="region"
                aria-labelledby={titleId}
                className={cn(
                  "gap-0 rounded-[2px] bg-surface py-0 ring-1 ring-rule transition-[box-shadow]",
                  isHeld && "ring-ink",
                )}
              >
                <CardHeader className="flex items-start justify-between gap-2 border-b border-rule px-4 pt-3 pb-3">
                  <div className="min-w-0">
                    <CardTitle className="text-sm leading-5 font-bold text-ink">
                      <h2 id={titleId}>{widget.title}</h2>
                    </CardTitle>
                    {widget.description && (
                      <CardDescription className="mt-0.5 text-xs leading-4 text-ink-3">
                        {widget.description}
                      </CardDescription>
                    )}
                  </div>
                  <button
                    type="button"
                    ref={(el) => {
                      if (el) grips.current.set(id, el);
                      else grips.current.delete(id);
                    }}
                    aria-label={`Move ${widget.title}`}
                    aria-describedby="widget-rail-help"
                    onPointerDown={down(id)}
                    onPointerMove={move}
                    onPointerUp={up}
                    onPointerCancel={up}
                    onLostPointerCapture={up}
                    onKeyDown={onKey(id)}
                    className={cn(
                      "-mr-1.5 hidden size-7 flex-none touch-none items-center justify-center rounded-[2px] text-ink-3 hover:bg-background hover:text-ink lg:inline-flex",
                      isHeld ? "cursor-grabbing" : "cursor-grab",
                    )}
                  >
                    <GripVertical aria-hidden className="size-4" strokeWidth={1.75} />
                  </button>
                </CardHeader>
                <CardContent className="px-4 py-3">{widget.body}</CardContent>
              </Card>
            </motion.li>
          );
        })}
      </ul>
      <p id="widget-rail-help" className="sr-only">
        Drag to reorder, or use the arrow keys, Home and End.
      </p>
      <p role="status" className="sr-only">
        {announcement}
      </p>
    </aside>
  );
}
