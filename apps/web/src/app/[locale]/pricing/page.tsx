"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import { redirectToCheckout } from "@/lib/stripe";
import { useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { AppFooter } from "@/components/footer";
import { Check, X, Loader2 } from "@/components/icons";

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
  const { user, profile, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [billingInterval, setBillingInterval] = useState<BillingInterval>("monthly");
  const [isLoading, setIsLoading] = useState<string | null>(null);

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
      router.push("/signup");
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

  const currentPlan = profile?.subscription?.plan || "free";

  // Define pricing plans
  const plans: Record<PlanType, PricingPlan> = {
    free: {
      name: t("free"),
      price: { monthly: 0 },
      priceId: {},
      description: t("freeDescription"),
      features: [
        { text: t("freeFeature1"), included: true },
        { text: t("freeFeature2"), included: true },
        { text: t("freeFeature3"), included: true },
        { text: t("proFeature1"), included: false },
        { text: t("proFeature2"), included: false },
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
        { text: t("proFeature1"), included: true },
        { text: t("proFeature2"), included: true },
        { text: t("proFeature3"), included: true },
        { text: t("proFeature5"), included: true },
        { text: t("premiumFeature2"), included: false },
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
        { text: t("premiumFeature1"), included: true },
        { text: t("premiumFeature2"), included: true },
        { text: t("premiumFeature3"), included: true },
        { text: t("premiumFeature4"), included: true },
      ],
      cta: t("upgradeTo", { plan: t("premium") }),
    },
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface pb-16 md:pb-0">
      <AppHeader activePage="pricing" />

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-12">
        <div className="text-center">
          <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            {t("title")}
          </h1>

          {/* Billing interval toggle - only shown for Pro plan */}
          <div className="mt-8 inline-flex items-center rounded-lg border border-border bg-white p-1 shadow-sm">
            <button
              onClick={() => setBillingInterval("monthly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                billingInterval === "monthly"
                  ? "bg-primary-600 text-white"
                  : "text-text-secondary hover:bg-surface-alt"
              }`}
            >
              {t("monthlyToggle")}
            </button>
            <button
              onClick={() => setBillingInterval("yearly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                billingInterval === "yearly"
                  ? "bg-primary-600 text-white"
                  : "text-text-secondary hover:bg-surface-alt"
              }`}
            >
              {t("yearlyToggle")}
              <span className="ml-1.5 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                {t("yearlySavings")}
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
            isAuthenticated={!!user}
          />

          {/* Pro Plan */}
          <PricingCard
            plan="pro"
            planData={plans.pro}
            currentPlan={currentPlan}
            billingInterval={billingInterval}
            isLoading={isLoading === "pro"}
            onUpgrade={() => handleUpgrade("pro", billingInterval)}
            isAuthenticated={!!user}
          />

          {/* Premium Plan */}
          <PricingCard
            plan="premium"
            planData={plans.premium}
            currentPlan={currentPlan}
            billingInterval={billingInterval}
            isLoading={isLoading === "premium"}
            onUpgrade={() => handleUpgrade("premium", "monthly")}
            isAuthenticated={!!user}
          />
        </div>
      </main>

      <MobileNav activePage="pricing" />
      <AppFooter />
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
  isAuthenticated: boolean;
}

function PricingCard({
  plan,
  planData,
  currentPlan,
  billingInterval,
  isLoading,
  onUpgrade,
  isAuthenticated,
}: PricingCardProps) {
  const t = useTranslations("pricing");
  const isCurrentPlan = currentPlan === plan;
  const price = billingInterval === "yearly" && planData.price.yearly
    ? planData.price.yearly
    : planData.price.monthly;
  const priceLabel = billingInterval === "yearly" && planData.price.yearly
    ? t("yearly")
    : t("monthly");

  // Determine card border styling based on plan type
  const getCardBorderClass = () => {
    if (plan === "premium") return "border-accent-500";
    if (planData.popular) return "border-primary-500 shadow-lg";
    return "border-border";
  };

  return (
    <div
      className={`relative rounded-2xl border-2 bg-white p-8 shadow-sm transition-all ${getCardBorderClass()} ${
        planData.popular ? "scale-105 md:scale-110" : ""
      }`}
    >
      {planData.popular && (
        <div className="absolute -top-4 left-0 right-0 flex justify-center">
          <span className="rounded-full bg-primary-500 px-4 py-1 text-xs font-semibold text-white shadow-md">
            {t("popularBadge")}
          </span>
        </div>
      )}

      {isAuthenticated && isCurrentPlan && (
        <div className="absolute right-4 top-4">
          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
            {t("currentPlan")}
          </span>
        </div>
      )}

      <div className="text-center">
        <h3 className="text-xl font-bold text-text-primary">{planData.name}</h3>
        <p className="mt-2 text-sm text-text-tertiary">{planData.description}</p>

        <div className="mt-6">
          <div className="flex items-baseline justify-center gap-1">
            <span className="font-display text-5xl font-bold text-text-primary">${price}</span>
            <span className="text-text-tertiary">{priceLabel}</span>
          </div>
          {billingInterval === "yearly" && planData.price.yearly && (
            <p className="mt-1 text-sm text-text-tertiary">
              ${Math.round(planData.price.yearly / 12)}{t("billedAnnually")}
            </p>
          )}
        </div>
      </div>

      <ul className="mt-8 space-y-3">
        {planData.features.map((feature, idx) => (
          <li key={idx} className="flex items-start gap-3">
            {feature.included ? (
              <Check className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
            ) : (
              <X className="mt-0.5 h-5 w-5 shrink-0 text-text-tertiary opacity-40" />
            )}
            <span
              className={`text-sm ${
                feature.included ? "text-text-secondary" : "text-text-tertiary line-through"
              }`}
            >
              {feature.text}
            </span>
          </li>
        ))}
      </ul>

      <button
        onClick={onUpgrade}
        disabled={(isAuthenticated && isCurrentPlan) || isLoading}
        className={`mt-8 w-full rounded-lg py-3 text-sm font-semibold transition-colors ${
          isAuthenticated && isCurrentPlan
            ? "cursor-not-allowed bg-surface-alt text-text-tertiary"
            : planData.popular
              ? "bg-primary-600 text-white hover:bg-primary-700"
              : "border-2 border-border bg-white text-text-secondary hover:border-primary-500 hover:text-primary-600"
        }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t("../common.loading")}
          </span>
        ) : isAuthenticated && isCurrentPlan ? (
          t("currentPlan")
        ) : !isAuthenticated && plan !== "free" ? (
          t("getStartedUnauthenticated")
        ) : (
          planData.cta
        )}
      </button>
    </div>
  );
}
