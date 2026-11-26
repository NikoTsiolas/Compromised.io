"use client";

// Header search, after the Bencho "seek" block (MIT): one object whose width is the state, with
// the lens fixed at an inset that centres it when shut and pads the field when open. Set as the
// design notes ask: corner 2, no cursor magnet (give 0), no glass, a hairline stroke. The spring
// is a CSS overshoot curve rather than the block's JS spring. The field is the shadcn Input.
// Phones get a plain link instead (see SiteHeader).
import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { Input } from "@/components/ui/input";

export function SearchField() {
  const router = useRouter();
  const field = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");

  return (
    <form
      role="search"
      action="/search"
      onSubmit={(e) => {
        e.preventDefault();
        const q = value.trim();
        if (q) router.push(`/search?q=${encodeURIComponent(q)}`);
      }}
      data-open={open || undefined}
      className="group/sek relative h-8 w-8 overflow-hidden rounded-[2px] border border-rule bg-background transition-[width] duration-[320ms] ease-[cubic-bezier(0.3,1.25,0.4,1)] data-open:w-64"
    >
      <Search
        aria-hidden
        className="pointer-events-none absolute top-1/2 left-[7px] size-4 -translate-y-1/2 text-ink-3 group-data-open/sek:text-ink-2"
        strokeWidth={1.75}
      />
      <Input
        ref={field}
        name="q"
        type="search"
        value={value}
        placeholder="Search companies, products, CVEs"
        aria-label="Search"
        tabIndex={open ? 0 : -1}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => {
          if (!value.trim()) setOpen(false);
        }}
        onKeyDown={(e) => {
          if (e.key !== "Escape") return;
          setValue("");
          setOpen(false);
          field.current?.blur();
        }}
        className="absolute inset-y-0 right-0 left-7 h-full rounded-none border-0 bg-transparent px-1 text-[13px] opacity-0 shadow-none transition-opacity duration-200 group-data-open/sek:opacity-100 focus-visible:ring-0 dark:bg-transparent"
      />
      {!open && (
        <button
          type="button"
          aria-label="Open search"
          className="absolute inset-0 cursor-pointer rounded-[inherit] transition-[scale] duration-150 active:scale-90"
          onClick={() => {
            setOpen(true);
            field.current?.focus();
          }}
        />
      )}
    </form>
  );
}
