import type { Metadata } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";

import "./globals.css";

const manrope = Manrope({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-body"
});

const mono = IBM_Plex_Mono({
  display: "swap",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-mono"
});

export const metadata: Metadata = {
  title: "Job Focus Dashboard",
  description: "Monorepo dashboard scaffold for profile, jobs, matches, and application tracking."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${manrope.variable} ${mono.variable}`}>{children}</body>
    </html>
  );
}
