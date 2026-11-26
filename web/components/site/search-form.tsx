"use client";

// The search page's form: the query and the filters (category, source, status, date range) on
// shadcn's Input, NativeSelect, Label and Button, set like the header field (hairline, corner 2,
// 13px). A GET form, so the URL is the search and it works before hydration; once hydrated it
// navigates on the client and leaves empty fields out of the URL. Choosing a filter applies it
// at once. Phones get native pickers and a two-column grid.
import { Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import type { FilterOption, SearchFilters, SearchQuery } from "@/lib/api";

const LABEL =
  "font-mono text-[11px] leading-4 font-medium tracking-[0.06em] text-ink-3 uppercase";
const CONTROL =
  "h-9 w-full rounded-[2px] border-rule bg-background text-[13px] dark:bg-background";

export function SearchForm({
  query,
  filters,
  clearHref,
}: {
  query: SearchQuery;
  /** Null when the filter values could not be loaded: the query alone still works. */
  filters: SearchFilters | null;
  /** The same query without filters, shown only when a filter is set. */
  clearHref?: string;
}) {
  const router = useRouter();
  const form = useRef<HTMLFormElement>(null);
  const apply = () => form.current?.requestSubmit();

  return (
    <form
      ref={form}
      action="/search"
      role="search"
      aria-label="Search events"
      onSubmit={(e) => {
        e.preventDefault();
        const params = new URLSearchParams();
        for (const [key, value] of new FormData(e.currentTarget)) {
          const text = typeof value === "string" ? value.trim() : "";
          if (text) params.set(key, text);
        }
        router.push(params.size ? `/search?${params}` : "/search");
      }}
    >
      <div className="flex gap-2">
        <div className="relative min-w-0 flex-1">
          <Search
            aria-hidden
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-3"
            strokeWidth={1.75}
          />
          <Input
            name="q"
            type="search"
            defaultValue={query.q ?? ""}
            maxLength={200}
            placeholder="Company, product, CVE, threat actor or keyword"
            aria-label="Search events"
            className={`${CONTROL} h-11 pl-9 text-[15px]`}
          />
        </div>
        <Button
          type="submit"
          className="h-11 rounded-[2px] bg-ink px-4 text-[13px] font-medium text-background hover:bg-ink/90"
        >
          Search
        </Button>
      </div>

      {filters && (
        <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-3 sm:grid-cols-3 lg:grid-cols-5">
          <Filter
            name="category"
            label="Category"
            any="Any category"
            options={filters.categories}
            value={query.category}
            onChange={apply}
          />
          <Filter
            name="source"
            label="Source"
            any="Any source"
            options={filters.sources}
            value={query.source}
            onChange={apply}
          />
          <Filter
            name="status"
            label="Status"
            any="Any status"
            options={filters.statuses}
            value={query.status}
            onChange={apply}
          />
          <DateField name="from" label="From" value={query.from} />
          <DateField name="to" label="To" value={query.to} />
        </div>
      )}
      {clearHref && (
        <Link
          href={clearHref}
          className="mt-3 inline-block text-[13px] leading-[18px] font-medium text-ink-2 underline-offset-4 hover:text-ink hover:underline"
        >
          Clear filters
        </Link>
      )}
    </form>
  );
}

function Filter({
  name,
  label,
  any,
  options,
  value,
  onChange,
}: {
  name: string;
  label: string;
  any: string;
  options: FilterOption[];
  value?: string;
  onChange: () => void;
}) {
  const id = `filter-${name}`;
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <Label htmlFor={id} className={LABEL}>
        {label}
      </Label>
      <NativeSelect
        id={id}
        name={name}
        defaultValue={value ?? ""}
        onChange={onChange}
        className="w-full [&_select]:h-9 [&_select]:rounded-[2px] [&_select]:border-rule [&_select]:text-[13px]"
      >
        <NativeSelectOption value="">{any}</NativeSelectOption>
        {options.map((o) => (
          <NativeSelectOption key={o.id} value={o.id}>
            {o.label}
          </NativeSelectOption>
        ))}
      </NativeSelect>
    </div>
  );
}

function DateField({ name, label, value }: { name: string; label: string; value?: string }) {
  const id = `filter-${name}`;
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <Label htmlFor={id} className={LABEL}>
        {label}
      </Label>
      <Input id={id} name={name} type="date" defaultValue={value ?? ""} className={CONTROL} />
    </div>
  );
}
