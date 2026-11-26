"use client";

// The companies a reader watches (#16). Kept only in this browser: local storage when the
// browser allows it, otherwise memory for as long as the page is open. Nothing is sent to our
// server. Every storage access is wrapped, so a browser that refuses storage (private mode,
// blocked site data) still gets a working Watch button and Watching list.
import { useSyncExternalStore } from "react";

export const WATCH_KEY = "compromised:watching:v1";

let memory: string[] = [];
let snapshot: string[] | null = null;
const listeners = new Set<() => void>();
const EMPTY: string[] = [];

function read(): string[] {
  try {
    const raw = window.localStorage.getItem(WATCH_KEY);
    if (raw === null) return memory;
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value)
      ? [...new Set(value.filter((v): v is string => typeof v === "string" && v.length > 0))]
      : [];
  } catch {
    return memory;
  }
}

function write(next: string[]) {
  memory = next;
  snapshot = next;
  try {
    window.localStorage.setItem(WATCH_KEY, JSON.stringify(next));
  } catch {
    // Storage refused: the list lives in memory until the page closes.
  }
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  // Another tab changing the list.
  const onStorage = (e: StorageEvent) => {
    if (e.key !== WATCH_KEY) return;
    snapshot = null;
    listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function getSnapshot(): string[] {
  if (snapshot === null) snapshot = read();
  return snapshot;
}

/** The watched companies, in the order they were added. Empty on the server and at hydration. */
export function useWatchlist(): string[] {
  return useSyncExternalStore(subscribe, getSnapshot, () => EMPTY);
}

export function isWatched(list: string[], company: string): boolean {
  return list.includes(company);
}

export function watch(company: string) {
  const list = getSnapshot();
  if (!list.includes(company)) write([...list, company]);
}

export function unwatch(company: string) {
  write(getSnapshot().filter((c) => c !== company));
}

export function toggleWatch(company: string) {
  if (getSnapshot().includes(company)) unwatch(company);
  else watch(company);
}
