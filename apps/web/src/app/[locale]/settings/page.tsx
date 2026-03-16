"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import { doc, updateDoc, serverTimestamp, Timestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { AppFooter } from "@/components/footer";
import { Button } from "@/components/button";
import { Input } from "@/components/input";
import { DatePicker } from "@/components/date-picker";
import { Save, LogOut, Globe } from "@/components/icons";

const VISA_TYPES = [
  { value: "H-1B", label: "H-1B" },
  { value: "F-1", label: "F-1 / OPT" },
  { value: "Family", label: "Family-Based" },
  { value: "GreenCard", label: "Green Card" },
  { value: "Other", label: "Other" },
];

// Language options will be rendered using translation keys

export default function SettingsPage() {
  const t = useTranslations("settings");
  const tNav = useTranslations("nav");
  const tOnboarding = useTranslations("onboarding");
  const { user, profile, loading, signOut, refreshProfile } = useAuth();
  const router = useRouter();

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState("en");
  const [visaType, setVisaType] = useState("");
  const [visaExpiry, setVisaExpiry] = useState<Date | null>(null);
  const [priorityDate, setPriorityDate] = useState<Date | null>(null);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccessBanner, setShowSuccessBanner] = useState(false);

  // Redirect if not authenticated or onboarding incomplete
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && profile && !profile.onboardingComplete) {
      router.push("/onboarding");
    }
  }, [loading, user, profile, router]);

  // Load profile data into form
  useEffect(() => {
    if (profile && user) {
      setDisplayName(user.displayName || "");
      setLanguage(profile.language || "en");
      setVisaType(profile.visaType || "");
      setVisaExpiry(profile.visaExpiry ? new Date(profile.visaExpiry) : null);
      setPriorityDate(profile.priorityDate ? new Date(profile.priorityDate) : null);
    }
  }, [profile, user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsSaving(true);
    try {
      const userRef = doc(db, "users", user.uid);
      const updateData: Record<string, unknown> = {
        language,
        visaType,
        updatedAt: serverTimestamp(),
      };

      // Handle date fields
      updateData.visaExpiry = visaExpiry ? Timestamp.fromDate(visaExpiry) : null;
      updateData.priorityDate = priorityDate ? Timestamp.fromDate(priorityDate) : null;

      await updateDoc(userRef, updateData);
      await refreshProfile();

      // Show success banner
      setShowSuccessBanner(true);
      setTimeout(() => {
        setShowSuccessBanner(false);
      }, 3000);
    } catch (error) {
      console.error("Error saving settings:", error);
      alert("Failed to save settings. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleManageSubscription = async () => {
    if (!user || !profile) return;

    try {
      const res = await fetch("/api/stripe/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerId: profile.subscription?.stripeCustomerId,
          locale: profile.language,
        }),
      });
      const { url } = await res.json();
      if (url) window.location.href = url;
    } catch (error) {
      console.error("Error opening Stripe portal:", error);
    }
  };

  const handleSignOut = async () => {
    if (confirm(t("signOutConfirm"))) {
      await signOut();
      router.push("/");
    }
  };

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface pb-16 md:pb-0">
      {/* Success banner */}
      {showSuccessBanner && (
        <div className="fixed left-0 right-0 top-0 z-50 animate-[slideDown_0.3s_ease-out] bg-success px-4 py-3 text-center text-sm font-medium text-white">
          {t("saved")}
        </div>
      )}

      {/* Top nav */}
      <AppHeader activePage="settings" />

      {/* Main content */}
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
        <h1 className="font-[var(--font-display)] text-3xl text-text-primary">
          {t("title")}
        </h1>

        <form onSubmit={handleSave} className="mt-8 space-y-8">
          {/* Profile Section */}
          <section className="border-b border-border-strong pb-8">
            <h2 className="font-[var(--font-display)] text-xl text-text-primary">
              {t("profile")}
            </h2>

            <div className="mt-6 space-y-6">
              {/* Display Name */}
              <div>
                <label
                  htmlFor="displayName"
                  className="block text-sm font-medium text-text-secondary"
                >
                  {t("displayName")}
                </label>
                <Input
                  type="text"
                  id="displayName"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Your name"
                  disabled
                  className="mt-2"
                />
                <p className="mt-2 text-xs text-text-tertiary">
                  Display name cannot be changed after signup
                </p>
              </div>

              {/* Language */}
              <div>
                <label
                  htmlFor="language"
                  className="flex items-center gap-2 text-sm font-medium text-text-secondary"
                >
                  <Globe className="h-4 w-4" />
                  {t("language")}
                </label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="mt-2 block w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="en">{t("languages.en")}</option>
                  <option value="es">{t("languages.es")}</option>
                </select>
              </div>

              {/* Visa Type */}
              <div>
                <label
                  htmlFor="visaType"
                  className="block text-sm font-medium text-text-secondary"
                >
                  {t("visaType")}
                </label>
                <select
                  id="visaType"
                  value={visaType}
                  onChange={(e) => setVisaType(e.target.value)}
                  className="mt-2 block w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="">{t("selectVisaType")}</option>
                  {VISA_TYPES.map((visa) => (
                    <option key={visa.value} value={visa.value}>
                      {tOnboarding(`visaTypes.${visa.value}`)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Visa Expiry Date */}
              <DatePicker
                label={t("visaExpiry")}
                value={visaExpiry}
                onChange={setVisaExpiry}
                placeholder={t("selectDate")}
              />

              {/* Priority Date */}
              <DatePicker
                label={t("priorityDate")}
                value={priorityDate}
                onChange={setPriorityDate}
                placeholder={t("selectDate")}
              />
            </div>
          </section>

          {/* Subscription Section */}
          <section className="border-b border-border-strong pb-8">
            <h2 className="font-[var(--font-display)] text-xl text-text-primary">
              {t("subscription")}
            </h2>

            <div className="mt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text-secondary">
                    {t("currentPlan")}
                  </p>
                  <p className="mt-1 text-lg font-semibold capitalize text-text-primary">
                    {profile.subscription.plan}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-sm font-medium ${
                    profile.subscription.cancelAt
                      ? "bg-warning/10 text-warning"
                      : profile.subscription.plan === "free"
                        ? "bg-surface-alt text-text-secondary"
                        : "bg-success/10 text-success"
                  }`}
                >
                  {profile.subscription.cancelAt ? "Canceling" : profile.subscription.status}
                </span>
              </div>

              {profile.subscription.cancelAt && (
                <p className="mt-3 text-sm text-warning">
                  {t("canceledNotice", {
                    date: new Date(profile.subscription.cancelAt._seconds * 1000).toLocaleDateString(),
                  })}
                </p>
              )}

              {profile.subscription.plan === "free" ? (
                <Link
                  href="/pricing"
                  className="mt-6 inline-block rounded-lg bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700"
                >
                  {t("upgradeToPro")}
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={handleManageSubscription}
                  className="mt-6 inline-block rounded-lg border border-border bg-surface px-6 py-3 text-sm font-semibold text-text-primary shadow-sm transition-colors hover:bg-surface-alt"
                >
                  {profile.subscription.cancelAt ? t("resubscribe") : t("manageSubscription")}
                </button>
              )}
            </div>
          </section>

          {/* Account Section */}
          <section className="pb-8">
            <h2 className="font-[var(--font-display)] text-xl text-text-primary">
              {t("account")}
            </h2>

            <div className="mt-6">
              <label className="block text-sm font-medium text-text-secondary">
                {t("email")}
              </label>
              <Input
                type="email"
                value={user.email || ""}
                disabled
                className="mt-2 bg-surface-alt text-text-tertiary"
              />
              <p className="mt-2 text-xs text-text-tertiary">
                Email address cannot be changed
              </p>
            </div>
          </section>

          {/* Action Buttons */}
          <div className="flex items-center justify-between border-t border-border-strong pt-8">
            <Button
              type="submit"
              variant="primary"
              disabled={isSaving}
              className="inline-flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  {t("saving")}
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {t("save")}
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={handleSignOut}
              className="inline-flex items-center gap-2 text-danger hover:bg-red-50"
            >
              <LogOut className="h-4 w-4" />
              {tNav("signOut")}
            </Button>
          </div>
        </form>
      </main>

      {/* Mobile bottom nav */}
      <MobileNav activePage="settings" />

      {/* Footer */}
      <AppFooter />
    </div>
  );
}
