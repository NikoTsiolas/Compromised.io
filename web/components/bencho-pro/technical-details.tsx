"use client";

// The inline "Technical details" expand on each row. State and accessibility come from the
// shadcn Collapsible (Base UI); the opening motion is the Bencho faq-accordion technique: the
// panel sits in a grid row that eases 0fr -> 1fr, so the row grows by exactly the panel's own
// height with nothing measured. Its word-by-word blur reveal was left out as decorative.
import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export function TechnicalDetails({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="contents">
      <CollapsibleTrigger className="group/td -my-3 inline-flex min-h-11 cursor-pointer items-center gap-1 text-[13px] leading-[18px] text-ink-3 underline-offset-4 hover:text-ink hover:underline sm:my-0 sm:min-h-0">
        Technical details
        <ChevronDown
          aria-hidden
          className="size-3.5 transition-[rotate] duration-[240ms] ease-[cubic-bezier(0.22,1,0.36,1)] group-data-[panel-open]/td:rotate-180"
        />
      </CollapsibleTrigger>
      <div
        data-open={open || undefined}
        className="col-span-full grid basis-full grid-rows-[0fr] transition-[grid-template-rows] duration-[240ms] ease-[cubic-bezier(0.22,1,0.36,1)] data-open:grid-rows-[1fr]"
      >
        <div className="min-h-0 overflow-hidden">
          <CollapsibleContent>{children}</CollapsibleContent>
        </div>
      </div>
    </Collapsible>
  );
}
