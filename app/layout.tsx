import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CompatibilityWarning } from "@/components/compatibility-warning";
import { SessionProvider } from "@/components/session-management/session-provider";
import { ThemeToggle } from "@/components/theme-toggle";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Expense Reconciliation System",
  description: "Upload and reconcile credit card statements with expense reports",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <SessionProvider>
          <div className="min-h-screen">
            <header className="fixed top-4 right-4 z-40">
              <ThemeToggle />
            </header>
            <CompatibilityWarning className="sticky top-0 z-50" />
            {children}
          </div>
        </SessionProvider>
      </body>
    </html>
  );
}
