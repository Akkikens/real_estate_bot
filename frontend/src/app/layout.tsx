import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { DM_Sans, Playfair_Display } from "next/font/google";
import { Providers } from "@/components/providers";
import { CookieConsent } from "@/components/cookie-consent";
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
  metadataBase: new URL("https://housematch.io"),
  title: {
    default: "HouseMatch — Your AI Property Scout",
    template: "%s | HouseMatch",
  },
  description:
    "Personalized property scores for Bay Area house-hackers and first-time investors. Get the top 5 deals delivered daily.",
  keywords: [
    "house hack",
    "bay area real estate",
    "property scoring",
    "first time home buyer",
    "investment property",
    "ADU",
    "oakland real estate",
    "fremont homes",
    "BART proximity",
  ],
  authors: [{ name: "HouseMatch" }],
  creator: "HouseMatch",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://housematch.io",
    siteName: "HouseMatch",
    title: "HouseMatch — Your AI Property Scout",
    description:
      "Personalized property scores for Bay Area house-hackers. 1,400+ properties scored daily.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "HouseMatch — AI-powered property scoring",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "HouseMatch — Your AI Property Scout",
    description:
      "Personalized property scores for Bay Area house-hackers.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
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
          <Providers>
            {children}
            <CookieConsent />
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
