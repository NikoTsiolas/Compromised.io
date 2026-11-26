"use client";

// Light/dark switch, after the Bencho theme-switch block (Pro licence: used here, not
// redistributed as a block). Restyled per the design notes: 64x32 with a hairline instead of a
// white pill, a 24px ink disc, 14px icons, and none of its frame painting. next-themes owns the
// theme; like the block, the switch reads the page's theme from the root element, so it can
// never disagree with what is on screen.
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
  return () => observer.disconnect();
}

const pageIsDark = () => document.documentElement.classList.contains("dark");

export function ThemeSwitch() {
  const { setTheme } = useTheme();
  const dark = useSyncExternalStore(subscribe, pageIsDark, () => false);

  return (
    <button
      type="button"
      role="switch"
      aria-checked={dark}
      aria-label="Dark theme"
      onClick={() => setTheme(dark ? "light" : "dark")}
      className="group/thm relative block h-8 w-16 shrink-0 cursor-pointer rounded-full border border-rule bg-background p-0 [-webkit-tap-highlight-color:transparent]"
    >
      <span
        aria-hidden
        className="absolute top-[3px] left-[3px] size-6 rounded-full bg-ink transition-[translate,scale] duration-[420ms] ease-[cubic-bezier(0.24,1.34,0.38,1)] group-active/thm:scale-90 dark:translate-x-8"
      />
      <span
        aria-hidden
        className="absolute top-[3px] left-[3px] grid size-6 place-items-center text-background transition-colors duration-[420ms] dark:text-ink-3"
      >
        <Sun className="size-3.5" strokeWidth={2} />
      </span>
      <span
        aria-hidden
        className="absolute top-[3px] right-[3px] grid size-6 place-items-center text-ink-3 transition-colors duration-[420ms] dark:text-background"
      >
        <Moon className="size-3.5" strokeWidth={2} />
      </span>
    </button>
  );
}
