"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import { redirectToCheckout } from "@/lib/stripe";
import LanguageSwitcher from "@/components/language-switcher";
import { useSearchParams } from "next/navigation";

// Stripe price IDs - TODO: Replace with your actual Stripe price IDs from the Stripe Dashboard
const PRICE_IDS = {
  proMonthly: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO_MONTHLY || "price_xxx_pro_monthly",
  proYearly: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO_YEARLY || "price_xxx_pro_yearly",
  premiumMonthly: process.env.NEXT_PUBLIC_STRIPE_PRICE_PREMIUM_MONTHLY || "price_xxx_premium_monthly",
};

type PlanType = "free" | "pro" | "premium";
type BillingInterval = "monthly" | "yearly";

interface PlanFeature {
  text: string;
  included: boolean;
}

interface PricingPlan {
  name: string;
  price: {
    monthly: number;
    yearly?: number;
  };
  priceId: {
    monthly?: string;
    yearly?: string;
  };
  description: string;
  features: PlanFeature[];
  popular?: boolean;
  cta: string;
}

export default function PricingPage() {
  const t = useTranslations("pricing");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const { user, profile, loading, signOut } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [billingInterval, setBillingInterval] = useState<BillingInterval>("monthly");
  const [isLoading, setIsLoading] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  // Show payment status alerts
  useEffect(() => {
    const payment = searchParams.get("payment");
    if (payment === "success") {
      // TODO: Show success toast/banner
      console.log("Payment successful!");
    } else if (payment === "cancelled") {
      // TODO: Show cancelled toast/banner
      console.log("Payment cancelled");
    }
  }, [searchParams]);

  const handleUpgrade = async (plan: PlanType, interval: BillingInterval) => {
    if (!user) {
      router.push("/login");
      return;
    }

    let priceId: string;

    if (plan === "pro") {
      priceId = interval === "yearly" ? PRICE_IDS.proYearly : PRICE_IDS.proMonthly;
    } else if (plan === "premium") {
      priceId = PRICE_IDS.premiumMonthly;
    } else {
      return; // Free plan, no action needed
    }

    setIsLoading(plan);

    try {
      // Get current locale from URL
      const locale = window.location.pathname.split("/")[1] || "en";
      await redirectToCheckout(priceId, locale, user.uid);
    } catch (error) {
      console.error("Error upgrading:", error);
      alert("Failed to start checkout. Please try again.");
      setIsLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const currentPlan = profile?.subscription?.plan || "free";

  // Define pricing plans
  const plans: Record<PlanType, PricingPlan> = {
    free: {
      name: t("free"),
      price: { monthly: 0 },
      priceId: {},
      description: t("freeDescription"),
      features: [
        { text: "10 messages per month", included: true },
        { text: "English only", included: true },
        { text: "Basic dashboard", included: true },
        { text: "Unlimited messages", included: false },
        { text: "English + Spanish", included: false },
      ],
      cta: t("currentPlan"),
    },
    pro: {
      name: t("pro"),
      price: {
        monthly: 19,
        yearly: 190,
      },
      priceId: {
        monthly: PRICE_IDS.proMonthly,
        yearly: PRICE_IDS.proYearly,
      },
      description: t("proDescription"),
      features: [
        { text: "Unlimited messages", included: true },
        { text: "English + Spanish", included: true },
        { text: "Full dashboard", included: true },
        { text: "Priority alerts", included: true },
        { text: "Family profiles", included: false },
      ],
      popular: true,
      cta: t("upgradeTo", { plan: t("pro") }),
    },
    premium: {
      name: t("premium"),
      price: { monthly: 39 },
      priceId: {
        monthly: PRICE_IDS.premiumMonthly,
      },
      description: t("premiumDescription"),
      features: [
        { text: "Everything in Pro", included: true },
        { text: "Family profiles", included: true },
        { text: "Priority attorney matching", included: true },
        { text: "Dedicated support", included: true },
      ],
      cta: t("upgradeTo", { plan: t("premium") }),
    },
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 pb-16 md:pb-0">
      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/dashboard">
            <span className="text-xl font-bold text-blue-700">Migravio</span>
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("dashboard")}
            </Link>
            <Link
              href="/chat"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("chat")}
            </Link>
            <Link
              href="/attorneys"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("attorneys")}
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <button
              onClick={signOut}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              {tNav("signOut")}
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-12">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
            {t("title")}
          </h1>

          {/* Billing interval toggle - only shown for Pro plan */}
          <div className="mt-8 inline-flex items-center rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
            <button
              onClick={() => setBillingInterval("monthly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                billingInterval === "monthly"
                  ? "bg-blue-600 text-white"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval("yearly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                billingInterval === "yearly"
                  ? "bg-blue-600 text-white"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              Yearly
              <span className="ml-1.5 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                Save $38
              </span>
            </button>
          </div>
        </div>

        {/* Pricing cards */}
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {/* Free Plan */}
          <PricingCard
            plan="free"
            planData={plans.free}
            currentPlan={currentPlan}
            billingInterval={billingInterval}
            isLoading={isLoading === "free"}
            onUpgrade={() => {}}
          />

          {/* Pro Plan */}
          <PricingCard
            plan="pro"
            planData={plans.pro}
            currentPlan={currentPlan}
            billingInterval={billingInterval}
            isLoading={isLoading === "pro"}
            onUpgrade={() => handleUpgrade("pro", billingInterval)}
          />

          {/* Premium Plan */}
          <PricingCard
            plan="premium"
            planData={plans.premium}
            currentPlan={currentPlan}
            billingInterval={billingInterval}
            isLoading={isLoading === "premium"}
            onUpgrade={() => handleUpgrade("premium", "monthly")}
          />
        </div>
      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white md:hidden">
        <div className="flex justify-around py-2">
          <Link
            href="/dashboard"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            {tNav("dashboard")}
          </Link>
          <Link
            href="/chat"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            {tNav("chat")}
          </Link>
          <Link
            href="/attorneys"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {tNav("attorneys")}
          </Link>
        </div>
      </nav>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50 py-6 text-center text-sm text-gray-500 md:block">
        {tFooter("disclaimer")}
      </footer>
    </div>
  );
}

// Pricing Card Component
interface PricingCardProps {
  plan: PlanType;
  planData: PricingPlan;
  currentPlan: PlanType;
  billingInterval: BillingInterval;
  isLoading: boolean;
  onUpgrade: () => void;
}

function PricingCard({
  plan,
  planData,
  currentPlan,
  billingInterval,
  isLoading,
  onUpgrade,
}: PricingCardProps) {
  const t = useTranslations("pricing");
  const isCurrentPlan = currentPlan === plan;
  const price = billingInterval === "yearly" && planData.price.yearly
    ? planData.price.yearly
    : planData.price.monthly;
  const priceLabel = billingInterval === "yearly" && planData.price.yearly
    ? t("yearly")
    : t("monthly");

  return (
    <div
      className={`relative rounded-2xl border-2 bg-white p-8 shadow-sm transition-all ${
        planData.popular
          ? "scale-105 border-blue-500 shadow-lg md:scale-110"
          : "border-gray-200"
      }`}
    >
      {planData.popular && (
        <div className="absolute -top-4 left-0 right-0 flex justify-center">
          <span className="rounded-full bg-blue-500 px-4 py-1 text-xs font-semibold text-white shadow-md">
            Most Popular
          </span>
        </div>
      )}

      {isCurrentPlan && (
        <div className="absolute right-4 top-4">
          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
            {t("currentPlan")}
          </span>
        </div>
      )}

      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-900">{planData.name}</h3>
        <p className="mt-2 text-sm text-gray-500">{planData.description}</p>

        <div className="mt-6">
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-5xl font-bold text-gray-900">${price}</span>
            <span className="text-gray-500">{priceLabel}</span>
          </div>
          {billingInterval === "yearly" && planData.price.yearly && (
            <p className="mt-1 text-sm text-gray-500">
              ${Math.round(planData.price.yearly / 12)}/month billed annually
            </p>
          )}
        </div>
      </div>

      <ul className="mt-8 space-y-3">
        {planData.features.map((feature, idx) => (
          <li key={idx} className="flex items-start gap-3">
            <svg
              className={`mt-0.5 h-5 w-5 shrink-0 ${
                feature.included ? "text-green-500" : "text-gray-300"
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={feature.included ? "M5 13l4 4L19 7" : "M6 18L18 6M6 6l12 12"}
              />
            </svg>
            <span
              className={`text-sm ${
                feature.included ? "text-gray-700" : "text-gray-400 line-through"
              }`}
            >
              {feature.text}
            </span>
          </li>
        ))}
      </ul>

      <button
        onClick={onUpgrade}
        disabled={isCurrentPlan || isLoading}
        className={`mt-8 w-full rounded-lg py-3 text-sm font-semibold transition-colors ${
          isCurrentPlan
            ? "cursor-not-allowed bg-gray-100 text-gray-400"
            : planData.popular
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "border-2 border-gray-300 bg-white text-gray-700 hover:border-blue-500 hover:text-blue-600"
        }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="h-4 w-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Loading...
          </span>
        ) : isCurrentPlan ? (
          t("currentPlan")
        ) : (
          planData.cta
        )}
      </button>
    </div>
  );
}
