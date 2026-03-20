import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { DM_Serif_Display, DM_Sans } from "next/font/google";
import { routing } from "@/i18n/routing";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/lib/theme-context";
import PWARegister from "@/components/pwa-register";
import GoogleAnalytics from "@/components/google-analytics";
import { Analytics } from "@vercel/analytics/react";
import "../globals.css";

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin", "latin-ext"],
  variable: "--font-dm-serif-display",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-dm-sans",
  display: "swap",
});

// SEO-optimized metadata with Open Graph and Twitter cards
export const metadata: Metadata = {
  title: {
    default: "Migravio - Navigate U.S. Immigration in Your Language",
    template: "%s | Migravio",
  },
  description:
    "AI-powered immigration assistant that answers 80% of your questions instantly. For the complex 20%, we connect you with vetted attorneys. Available in English and Spanish.",
  keywords: [
    "immigration",
    "visa",
    "H-1B",
    "green card",
    "immigration attorney",
    "USCIS",
    "immigration help",
    "visa status",
    "immigration AI",
    "Spanish immigration help",
  ],
  authors: [{ name: "Migravio" }],
  creator: "Migravio",
  publisher: "Migravio",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    alternateLocale: ["es_US"],
    url: "https://migravio.com",
    siteName: "Migravio",
    title: "Migravio - Navigate U.S. Immigration in Your Language",
    description:
      "AI-powered immigration assistant that answers 80% of your questions instantly. For the complex 20%, we connect you with vetted attorneys.",
    images: [
      {
        url: "https://migravio.com/og-image.png",
        width: 1200,
        height: 630,
        alt: "Migravio - Your Trusted Immigration Guide",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Migravio - Navigate U.S. Immigration in Your Language",
    description:
      "AI-powered immigration assistant that answers 80% of your questions instantly. For the complex 20%, we connect you with vetted attorneys.",
    images: ["https://migravio.com/og-image.png"],
    creator: "@migravio",
  },
  alternates: {
    canonical: "https://migravio.com",
    languages: {
      en: "https://migravio.com/en",
      es: "https://migravio.com/es",
    },
  },
  verification: {
    google: "your-google-verification-code",
  },
  category: "Legal Technology",
  applicationName: "Migravio",
  appleWebApp: {
    capable: true,
    title: "Migravio",
    statusBarStyle: "default",
  },
  formatDetection: {
    telephone: false,
  },
  other: {
    "application-name": "Migravio",
  },
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        {/* Anti-flash: apply dark class before React hydrates */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('migravio_theme');if(t==='dark')document.documentElement.classList.add('dark');if(t==='system'&&window.matchMedia('(prefers-color-scheme:dark)').matches)document.documentElement.classList.add('dark')}catch(e){}})()`,
          }}
        />
        {/* Favicon & PWA icons */}
        <link rel="icon" href="/favicon.ico" sizes="32x32" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />

        {/* PWA manifest */}
        <link rel="manifest" href="/manifest.json" />

        {/* Canonical URL */}
        <link rel="canonical" href={`https://migravio.com/${locale}`} />

        {/* Preconnect to external domains for better performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />

        {/* Theme color for mobile browsers - Deep Indigo */}
        <meta name="theme-color" content="#3730a3" />

        {/* iOS Web App configuration */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Migravio" />

        {/* Structured data for better SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebApplication",
              name: "Migravio",
              description:
                "AI-powered immigration assistant for navigating the U.S. immigration system",
              url: "https://migravio.com",
              applicationCategory: "LegalService",
              offers: {
                "@type": "AggregateOffer",
                lowPrice: "0",
                highPrice: "39",
                priceCurrency: "USD",
              },
              inLanguage: ["en-US", "es-US"],
              operatingSystem: "Any",
            }),
          }}
        />
      </head>
      <body className={`${dmSerifDisplay.variable} ${dmSans.variable} font-sans antialiased`}>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <AuthProvider>
              <PWARegister />
              {children}
            </AuthProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
        <GoogleAnalytics />
        <Analytics />
      </body>
    </html>
  );
}
