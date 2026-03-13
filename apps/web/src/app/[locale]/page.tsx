"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import LanguageSwitcher from "@/components/language-switcher";

export default function LandingPage() {
  const t = useTranslations();

  // Smooth scroll handler for "Learn More" button
  const scrollToFeatures = () => {
    const featuresSection = document.getElementById("features");
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Header / Navigation */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="text-xl font-bold text-blue-700">
            {t("common.appName")}
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <Link
              href="/login"
              className="hidden px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 sm:inline-block"
            >
              {t("auth.login")}
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              {t("auth.signup")}
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 to-white px-4 py-20 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
              {t("landing.hero.headline")}
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-gray-600 sm:text-xl">
              {t("landing.hero.subheadline")}
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/signup"
                className="w-full rounded-lg bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-sm hover:bg-blue-700 sm:w-auto"
              >
                {t("landing.hero.ctaPrimary")}
              </Link>
              <button
                onClick={scrollToFeatures}
                className="w-full rounded-lg border border-gray-300 bg-white px-8 py-3.5 text-base font-semibold text-gray-900 hover:bg-gray-50 sm:w-auto"
              >
                {t("landing.hero.ctaSecondary")}
              </button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                {t("landing.features.title")}
              </h2>
            </div>
            <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {/* Feature 1: AI Assistant */}
              <div className="flex flex-col rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-2xl">
                  💬
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.features.aiAssistant.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.features.aiAssistant.description")}
                </p>
              </div>

              {/* Feature 2: Dashboard */}
              <div className="flex flex-col rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-2xl">
                  📊
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.features.dashboard.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.features.dashboard.description")}
                </p>
              </div>

              {/* Feature 3: Attorneys */}
              <div className="flex flex-col rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-2xl">
                  ⚖️
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.features.attorneys.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.features.attorneys.description")}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="bg-gray-50 px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                {t("landing.howItWorks.title")}
              </h2>
            </div>
            <div className="mt-16 grid gap-12 sm:grid-cols-3">
              {/* Step 1 */}
              <div className="relative text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-2xl font-bold text-white">
                  1
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.howItWorks.step1.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.howItWorks.step1.description")}
                </p>
              </div>

              {/* Step 2 */}
              <div className="relative text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-2xl font-bold text-white">
                  2
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.howItWorks.step2.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.howItWorks.step2.description")}
                </p>
              </div>

              {/* Step 3 */}
              <div className="relative text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-2xl font-bold text-white">
                  3
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {t("landing.howItWorks.step3.title")}
                </h3>
                <p className="mt-4 text-base text-gray-600">
                  {t("landing.howItWorks.step3.description")}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Preview Section */}
        <section className="px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                {t("landing.pricingPreview.title")}
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                {t("landing.pricingPreview.subtitle")}
              </p>
            </div>
            <div className="mt-12 grid gap-8 sm:grid-cols-3">
              {/* Free Plan */}
              <div className="flex flex-col rounded-2xl border-2 border-gray-200 bg-white p-8">
                <h3 className="text-2xl font-bold text-gray-900">
                  {t("pricing.free")}
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  {t("pricing.freeDescription")}
                </p>
                <p className="mt-6 text-4xl font-bold text-gray-900">$0</p>
                <ul className="mt-8 space-y-3">
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      10 messages per month
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">English only</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">Basic dashboard</span>
                  </li>
                </ul>
                <Link
                  href="/signup"
                  className="mt-8 rounded-lg border border-blue-600 bg-white px-6 py-3 text-center text-sm font-semibold text-blue-600 hover:bg-blue-50"
                >
                  {t("common.getStarted")}
                </Link>
              </div>

              {/* Pro Plan - Featured */}
              <div className="relative flex flex-col rounded-2xl border-2 border-blue-600 bg-white p-8 shadow-lg">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-sm font-semibold text-white">
                  Popular
                </div>
                <h3 className="text-2xl font-bold text-gray-900">
                  {t("pricing.pro")}
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  {t("pricing.proDescription")}
                </p>
                <p className="mt-6">
                  <span className="text-4xl font-bold text-gray-900">$19</span>
                  <span className="text-gray-600">/month</span>
                </p>
                <ul className="mt-8 space-y-3">
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      Unlimited messages
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      English + Spanish
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">Full dashboard</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">Priority alerts</span>
                  </li>
                </ul>
                <Link
                  href="/signup"
                  className="mt-8 rounded-lg bg-blue-600 px-6 py-3 text-center text-sm font-semibold text-white hover:bg-blue-700"
                >
                  {t("common.getStarted")}
                </Link>
              </div>

              {/* Premium Plan */}
              <div className="flex flex-col rounded-2xl border-2 border-gray-200 bg-white p-8">
                <h3 className="text-2xl font-bold text-gray-900">
                  {t("pricing.premium")}
                </h3>
                <p className="mt-2 text-sm text-gray-600">
                  {t("pricing.premiumDescription")}
                </p>
                <p className="mt-6">
                  <span className="text-4xl font-bold text-gray-900">$39</span>
                  <span className="text-gray-600">/month</span>
                </p>
                <ul className="mt-8 space-y-3">
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      Everything in Pro
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">Family profiles</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      Priority attorney matching
                    </span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-3 text-green-500">✓</span>
                    <span className="text-sm text-gray-700">
                      Dedicated support
                    </span>
                  </li>
                </ul>
                <Link
                  href="/signup"
                  className="mt-8 rounded-lg border border-blue-600 bg-white px-6 py-3 text-center text-sm font-semibold text-blue-600 hover:bg-blue-50"
                >
                  {t("common.getStarted")}
                </Link>
              </div>
            </div>
            <div className="mt-12 text-center">
              <Link
                href="/pricing"
                className="text-base font-semibold text-blue-600 hover:text-blue-700"
              >
                {t("landing.pricingPreview.ctaViewPricing")} →
              </Link>
            </div>
          </div>
        </section>

        {/* Trust Section */}
        <section className="bg-blue-50 px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                {t("landing.trust.title")}
              </h2>
            </div>
            <div className="mt-16 grid gap-8 sm:grid-cols-3">
              {/* Trust 1 */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-3xl">
                  📚
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {t("landing.trust.trust1.title")}
                </h3>
                <p className="mt-3 text-sm text-gray-600">
                  {t("landing.trust.trust1.description")}
                </p>
              </div>

              {/* Trust 2 */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-3xl">
                  🔒
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {t("landing.trust.trust2.title")}
                </h3>
                <p className="mt-3 text-sm text-gray-600">
                  {t("landing.trust.trust2.description")}
                </p>
              </div>

              {/* Trust 3 */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-3xl">
                  🤝
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {t("landing.trust.trust3.title")}
                </h3>
                <p className="mt-3 text-sm text-gray-600">
                  {t("landing.trust.trust3.description")}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              {t("landing.finalCta.title")}
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              {t("landing.finalCta.subtitle")}
            </p>
            <div className="mt-10">
              <Link
                href="/signup"
                className="inline-block rounded-lg bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-sm hover:bg-blue-700"
              >
                {t("landing.finalCta.cta")}
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {/* Brand */}
            <div className="col-span-2">
              <span className="text-xl font-bold text-blue-700">
                {t("common.appName")}
              </span>
              <p className="mt-4 text-sm text-gray-600">
                {t("landing.hero.subheadline")}
              </p>
            </div>

            {/* Links */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Product</h3>
              <ul className="mt-4 space-y-3">
                <li>
                  <Link
                    href="/pricing"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    {t("pricing.title")}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/signup"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    {t("auth.signup")}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Legal</h3>
              <ul className="mt-4 space-y-3">
                <li>
                  <Link
                    href="/terms"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    {t("footer.terms")}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/privacy"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    {t("footer.privacy")}
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Legal Disclaimer */}
          <div className="mt-12 border-t border-gray-200 pt-8">
            <p className="text-center text-sm text-gray-500">
              {t("footer.disclaimer")}
            </p>
            <p className="mt-2 text-center text-sm text-gray-400">
              © {new Date().getFullYear()} {t("common.appName")}. All rights
              reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
