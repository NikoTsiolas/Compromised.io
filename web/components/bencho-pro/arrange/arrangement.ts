// The reader's widget arrangement: which side the rail sits on and the widgets' order. Kept in
// this browser's local storage only. Every access is wrapped: a browser that refuses storage
// (private mode, blocked site data) gets the default arrangement and the page works the same.
// Part of the rail adapted from the Bencho "Reorder list" (Arrange) block; see ../README.md.

export type RailSide = "left" | "right";
export type Arrangement = { side: RailSide; order: string[] };

export const STORAGE_KEY = "compromised:widgets:v1";

/** Keep only known ids, each once, and append any widget the stored order does not know. */
export function normalise(value: unknown, ids: string[]): Arrangement {
  const fallback: Arrangement = { side: "right", order: [...ids] };
  if (!value || typeof value !== "object") return fallback;
  const v = value as { side?: unknown; order?: unknown };
  const side: RailSide = v.side === "left" ? "left" : "right";
  const stored = Array.isArray(v.order)
    ? v.order.filter((id): id is string => typeof id === "string" && ids.includes(id))
    : [];
  const order = [...new Set(stored)];
  for (const id of ids) if (!order.includes(id)) order.push(id);
  return { side, order };
}

export function load(ids: string[]): Arrangement {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return normalise(raw ? JSON.parse(raw) : null, ids);
  } catch {
    return normalise(null, ids);
  }
}

export function save(arrangement: Arrangement): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(arrangement));
  } catch {
    // Not kept; the arrangement still holds for this visit.
  }
}

/** Mirror the arrangement onto <html>, where the layout CSS reads it (see globals.css). */
export function apply(arrangement: Arrangement): void {
  const root = document.documentElement;
  root.dataset.railSide = arrangement.side;
  arrangement.order.forEach((id, i) => root.style.setProperty(`--widget-${id}`, String(i)));
}

/**
 * The same as load() + apply(), as a script that runs before first paint, so a stored
 * arrangement shows at once instead of jumping after hydration. It touches only <html>, whose
 * attributes React leaves alone (suppressHydrationWarning in app/layout.tsx).
 */
export function prePaintScript(ids: string[]): string {
  return `(function(){try{var ids=${JSON.stringify(ids)};var a=JSON.parse(localStorage.getItem(${JSON.stringify(
    STORAGE_KEY,
  )})||"null")||{};var r=document.documentElement;r.dataset.railSide=a.side==="left"?"left":"right";var o=(Array.isArray(a.order)?a.order:[]).filter(function(id,i,s){return ids.indexOf(id)>-1&&s.indexOf(id)===i});ids.forEach(function(id){if(o.indexOf(id)<0)o.push(id)});o.forEach(function(id,i){r.style.setProperty("--widget-"+id,String(i))})}catch(e){}})();`;
}
