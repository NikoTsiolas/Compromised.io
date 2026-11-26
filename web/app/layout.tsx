import type { Metadata, Viewport } from "next";
import { ThemeProvider } from "next-themes";

import "./globals.css";

export const metadata: Metadata = {
  title: "Compromised",
  description:
    "A plain-language feed of publicly reported security incidents.",
};

export const viewport: Viewport = {
  themeColor: "#ffffff",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // next-themes sets the theme class on <html> before hydration, hence the warning suppression.
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Without script, pictures show at once instead of waiting to fade in. */}
        <noscript>
          <style>{`.event-img{opacity:1}`}</style>
        </noscript>
      </head>
      <body className="min-h-dvh">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
