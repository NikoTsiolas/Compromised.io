import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Compromised",
  description:
    "A plain-language feed of publicly reported security incidents.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
