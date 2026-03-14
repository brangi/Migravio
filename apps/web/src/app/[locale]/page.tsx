"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Logo } from "@/components/logo";
import { Button } from "@/components/button";
import { LandingFooter } from "@/components/footer";
import {
  MessageCircle,
  BarChart3,
  Gavel,
  BookOpen,
  Shield,
  Handshake,
  ArrowRight,
  Check,
  X,
} from "@/components/icons";
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
    <div className="flex min-h-screen flex-col">
      {/* Header / Navigation */}
      <header className="sticky top-0 z-50 border-b border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="hover:opacity-80 transition-opacity">
            <Logo size="md" variant="full" />
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium">
            <button
              onClick={scrollToFeatures}
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              {t("landing.nav.features")}
            </button>
            <Link
              href="/pricing"
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              {t("landing.nav.pricing")}
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <Link href="/login" className="hidden sm:inline-block">
              <Button variant="ghost" size="sm">
                {t("auth.login")}
              </Button>
            </Link>
            <Link href="/signup">
              <Button variant="accent" size="sm">
                {t("landing.nav.getStarted")}
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section - Clean warm surface, no gradient */}
        <section className="relative overflow-hidden bg-surface-alt px-4 py-20 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className="font-[var(--font-display)] text-4xl font-bold tracking-tight text-text-primary sm:text-5xl md:text-6xl lg:text-7xl">
              {t("landing.hero.headline")}
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-text-secondary sm:text-xl">
              {t("landing.hero.subheadline")}
            </p>

            {/* CTA Buttons */}
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/signup">
                <Button variant="accent" size="lg" icon={<ArrowRight className="h-5 w-5" />}>
                  {t("landing.hero.ctaStart")}
                </Button>
              </Link>
              <Button variant="secondary" size="lg" onClick={scrollToFeatures}>
                {t("landing.hero.ctaSecondary")}
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-4 text-sm text-text-tertiary">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary-500" />
                <span>{t("landing.hero.trustBadge1")}</span>
              </div>
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-primary-500" />
                <span>{t("landing.hero.trustBadge2")}</span>
              </div>
              <div className="flex items-center gap-2">
                <Handshake className="h-4 w-4 text-primary-500" />
                <span>{t("landing.hero.trustBadge3")}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section - Asymmetric Layout */}
        <section id="features" className="px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="max-w-2xl">
              <h2 className="font-[var(--font-display)] text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
                {t("landing.features.title")}
              </h2>
              <p className="mt-4 text-lg text-text-secondary">
                {t("landing.features.subtitle")}
              </p>
            </div>

            {/* Asymmetric Grid - Large + Two Stacked */}
            <div className="mt-16 grid gap-8 lg:grid-cols-3 animate-stagger">
              {/* Large Feature: AI Chat (2/3 width on large screens) */}
              <div className="lg:col-span-2 flex flex-col rounded-2xl border border-border bg-surface p-8 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                    <MessageCircle className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-semibold text-text-primary">
                      {t("landing.features.aiAssistant.title")}
                    </h3>
                    <p className="mt-3 text-base text-text-secondary leading-relaxed">
                      {t("landing.features.aiAssistant.description")}
                    </p>
                  </div>
                </div>

                {/* Visual Mock - Chat Preview */}
                <div className="mt-8 rounded-lg bg-surface-alt p-6 border border-border">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-1 rounded-lg bg-primary-50 border border-primary-200 p-3">
                        <p className="text-sm text-text-secondary">
                          "{t("landing.features.aiAssistant.mockQuestion")}"
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="flex-1 rounded-lg bg-accent-50 border border-accent-200 p-3">
                        <p className="text-sm text-text-secondary">
                          "{t("landing.features.aiAssistant.mockAnswer")}"
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stacked Features */}
              <div className="space-y-8">
                {/* Dashboard */}
                <div className="flex flex-col rounded-2xl border border-border bg-surface p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                    <BarChart3 className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 text-xl font-semibold text-text-primary">
                    {t("landing.features.dashboard.title")}
                  </h3>
                  <p className="mt-3 text-base text-text-secondary">
                    {t("landing.features.dashboard.description")}
                  </p>
                </div>

                {/* Attorney Referral */}
                <div className="flex flex-col rounded-2xl border border-border bg-surface p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                    <Gavel className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 text-xl font-semibold text-text-primary">
                    {t("landing.features.attorneys.title")}
                  </h3>
                  <p className="mt-3 text-base text-text-secondary">
                    {t("landing.features.attorneys.description")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section - Visual Path */}
        <section className="bg-surface-alt px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="font-[var(--font-display)] text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
                {t("landing.howItWorks.title")}
              </h2>
            </div>

            {/* Steps with connecting path */}
            <div className="mt-16 relative">
              {/* Connecting line - hidden on mobile */}
              <div className="hidden lg:block absolute top-8 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-200 via-accent-300 to-primary-200"
                   style={{ top: '2rem', margin: '0 12.5%' }}
              />

              <div className="grid gap-12 lg:grid-cols-3 animate-stagger">
                {/* Step 1 */}
                <div className="relative text-center">
                  <div className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary-600 text-2xl font-bold text-white shadow-lg z-10">
                    1
                  </div>
                  <h3 className="text-xl font-semibold text-text-primary font-[var(--font-display)]">
                    {t("landing.howItWorks.step1.title")}
                  </h3>
                  <p className="mt-4 text-base text-text-secondary">
                    {t("landing.howItWorks.step1.description")}
                  </p>
                </div>

                {/* Step 2 */}
                <div className="relative text-center">
                  <div className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-accent-500 text-2xl font-bold text-white shadow-lg z-10">
                    2
                  </div>
                  <h3 className="text-xl font-semibold text-text-primary font-[var(--font-display)]">
                    {t("landing.howItWorks.step2.title")}
                  </h3>
                  <p className="mt-4 text-base text-text-secondary">
                    {t("landing.howItWorks.step2.description")}
                  </p>
                </div>

                {/* Step 3 */}
                <div className="relative text-center">
                  <div className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary-600 text-2xl font-bold text-white shadow-lg z-10">
                    3
                  </div>
                  <h3 className="text-xl font-semibold text-text-primary font-[var(--font-display)]">
                    {t("landing.howItWorks.step3.title")}
                  </h3>
                  <p className="mt-4 text-base text-text-secondary">
                    {t("landing.howItWorks.step3.description")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Preview Section */}
        <section className="px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="font-[var(--font-display)] text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
                {t("landing.pricingPreview.title")}
              </h2>
              <p className="mt-4 text-lg text-text-secondary">
                {t("landing.pricingPreview.subtitle")}
              </p>
            </div>

            <div className="mt-12 grid gap-8 lg:grid-cols-3 animate-stagger">
              {/* Free Plan - Minimal styling */}
              <div className="flex flex-col rounded-2xl border border-border bg-surface p-8">
                <h3 className="text-2xl font-bold text-text-primary font-[var(--font-display)]">
                  {t("pricing.free")}
                </h3>
                <p className="mt-2 text-sm text-text-tertiary">
                  {t("pricing.freeDescription")}
                </p>
                <p className="mt-6 text-4xl font-bold text-text-primary">
                  <span className="font-[var(--font-display)]">$0</span>
                  <span className="text-base font-normal text-text-tertiary">/month</span>
                </p>

                <ul className="mt-8 space-y-3 flex-1">
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">
                      {t("pricing.freeFeature1")}
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.freeFeature2")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.freeFeature3")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <X className="h-5 w-5 flex-shrink-0 text-text-tertiary" />
                    <span className="text-sm text-text-tertiary">{t("pricing.freeFeature4")}</span>
                  </li>
                </ul>

                <Link href="/signup" className="mt-8">
                  <Button variant="secondary" size="md" className="w-full">
                    {t("common.getStarted")}
                  </Button>
                </Link>
              </div>

              {/* Pro Plan - Featured with primary border */}
              <div className="relative flex flex-col rounded-2xl border-2 border-primary-600 bg-surface p-8 shadow-lg">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-primary-600 px-4 py-1 text-sm font-semibold text-white">
                  {t("pricing.popularBadge")}
                </div>
                <h3 className="text-2xl font-bold text-text-primary font-[var(--font-display)]">
                  {t("pricing.pro")}
                </h3>
                <p className="mt-2 text-sm text-text-tertiary">
                  {t("pricing.proDescription")}
                </p>
                <p className="mt-6">
                  <span className="text-4xl font-bold text-text-primary font-[var(--font-display)]">$19</span>
                  <span className="text-base font-normal text-text-tertiary">/month</span>
                </p>

                <ul className="mt-8 space-y-3 flex-1">
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.proFeature1")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.proFeature2")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.proFeature3")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.proFeature4")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.proFeature5")}</span>
                  </li>
                </ul>

                <Link href="/signup" className="mt-8">
                  <Button variant="primary" size="md" className="w-full">
                    {t("common.getStarted")}
                  </Button>
                </Link>
              </div>

              {/* Premium Plan - Amber top border */}
              <div className="flex flex-col rounded-2xl border-t-4 border-t-accent-500 border-x border-b border-border bg-surface p-8 shadow-sm">
                <h3 className="text-2xl font-bold text-text-primary font-[var(--font-display)]">
                  {t("pricing.premium")}
                </h3>
                <p className="mt-2 text-sm text-text-tertiary">
                  {t("pricing.premiumDescription")}
                </p>
                <p className="mt-6">
                  <span className="text-4xl font-bold text-text-primary font-[var(--font-display)]">$39</span>
                  <span className="text-base font-normal text-text-tertiary">/month</span>
                </p>

                <ul className="mt-8 space-y-3 flex-1">
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.premiumFeature1")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.premiumFeature2")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.premiumFeature3")}</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-5 w-5 flex-shrink-0 text-success" />
                    <span className="text-sm text-text-secondary">{t("pricing.premiumFeature4")}</span>
                  </li>
                </ul>

                <Link href="/signup" className="mt-8">
                  <Button variant="accent" size="md" className="w-full">
                    {t("common.getStarted")}
                  </Button>
                </Link>
              </div>
            </div>

            <div className="mt-12 text-center">
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 text-base font-semibold text-primary-600 hover:text-primary-700 transition-colors"
              >
                {t("landing.pricingPreview.ctaViewPricing")}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Trust Section - Warm primary background */}
        <section className="bg-primary-50 px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="font-[var(--font-display)] text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
                {t("landing.trust.title")}
              </h2>
            </div>
            <div className="mt-16 grid gap-12 md:grid-cols-3">
              {/* Trust 1 - USCIS Data */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm border border-primary-200">
                  <BookOpen className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary">
                  {t("landing.trust.trust1.title")}
                </h3>
                <p className="mt-3 text-sm text-text-secondary">
                  {t("landing.trust.trust1.description")}
                </p>
              </div>

              {/* Trust 2 - Privacy */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm border border-primary-200">
                  <Shield className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary">
                  {t("landing.trust.trust2.title")}
                </h3>
                <p className="mt-3 text-sm text-text-secondary">
                  {t("landing.trust.trust2.description")}
                </p>
              </div>

              {/* Trust 3 - Expert Network */}
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm border border-primary-200">
                  <Handshake className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary">
                  {t("landing.trust.trust3.title")}
                </h3>
                <p className="mt-3 text-sm text-text-secondary">
                  {t("landing.trust.trust3.description")}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA Section - Dark primary background */}
        <section className="bg-primary-900 px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="font-[var(--font-display)] text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
              {t("landing.finalCta.title")}
            </h2>
            <p className="mt-6 text-lg text-primary-100">
              {t("landing.finalCta.subtitle")}
            </p>
            <div className="mt-10">
              <Link href="/signup">
                <Button
                  variant="accent"
                  size="lg"
                  icon={<ArrowRight className="h-5 w-5" />}
                  className="shadow-xl hover:shadow-2xl"
                >
                  {t("landing.finalCta.cta")}
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <LandingFooter />
    </div>
  );
}
