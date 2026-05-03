import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { DM_Sans, Playfair_Display } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const body = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

const heading = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-heading",
});

export const metadata: Metadata = {
  title: "HouseMatch — Your AI Property Scout",
  description:
    "Personalized property scoring for house-hackers and first-time investors. Get daily picks scored against your strategy.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className={`${body.variable} ${heading.variable}`}>
        <body className="grain font-[family-name:var(--font-sans)] min-h-screen">
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
