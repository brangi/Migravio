"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import { doc, updateDoc, serverTimestamp, Timestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import LanguageSwitcher from "@/components/language-switcher";

const VISA_TYPES = [
  { value: "H-1B", label: "H-1B" },
  { value: "F-1", label: "F-1 / OPT" },
  { value: "Family", label: "Family-Based" },
  { value: "GreenCard", label: "Green Card" },
  { value: "Other", label: "Other" },
];

const LANGUAGE_OPTIONS = [
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
];

export default function SettingsPage() {
  const t = useTranslations("settings");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const tOnboarding = useTranslations("onboarding");
  const { user, profile, loading, signOut, refreshProfile } = useAuth();
  const router = useRouter();

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState("en");
  const [visaType, setVisaType] = useState("");
  const [visaExpiry, setVisaExpiry] = useState("");
  const [priorityDate, setPriorityDate] = useState("");

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
      setVisaExpiry(
        profile.visaExpiry
          ? new Date(profile.visaExpiry).toISOString().split("T")[0]
          : ""
      );
      setPriorityDate(
        profile.priorityDate
          ? new Date(profile.priorityDate).toISOString().split("T")[0]
          : ""
      );
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
      if (visaExpiry) {
        updateData.visaExpiry = Timestamp.fromDate(new Date(visaExpiry));
      } else {
        updateData.visaExpiry = null;
      }

      if (priorityDate) {
        updateData.priorityDate = Timestamp.fromDate(new Date(priorityDate));
      } else {
        updateData.priorityDate = null;
      }

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
          customerId: (profile as unknown as Record<string, unknown>)
            ?.stripeCustomerId,
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
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 pb-16 md:pb-0">
      {/* Success banner */}
      {showSuccessBanner && (
        <div className="fixed left-0 right-0 top-0 z-50 animate-[slideDown_0.3s_ease-out] bg-green-600 px-4 py-3 text-center text-sm font-medium text-white">
          {t("saved")}
        </div>
      )}

      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <span className="text-xl font-bold text-blue-700">Migravio</span>
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
            <Link
              href="/settings"
              className="text-sm font-medium text-blue-600"
            >
              {tNav("settings")}
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <button
              onClick={handleSignOut}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              {tNav("signOut")}
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">{t("title")}</h1>

        <form onSubmit={handleSave} className="mt-6 space-y-6">
          {/* Profile Section */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("profile")}
            </h2>

            <div className="mt-4 space-y-4">
              {/* Display Name */}
              <div>
                <label
                  htmlFor="displayName"
                  className="block text-sm font-medium text-gray-700"
                >
                  {t("displayName")}
                </label>
                <input
                  type="text"
                  id="displayName"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Your name"
                  disabled
                />
                <p className="mt-1 text-xs text-gray-500">
                  Display name cannot be changed after signup
                </p>
              </div>

              {/* Language */}
              <div>
                <label
                  htmlFor="language"
                  className="block text-sm font-medium text-gray-700"
                >
                  {t("language")}
                </label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {LANGUAGE_OPTIONS.map((lang) => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Visa Type */}
              <div>
                <label
                  htmlFor="visaType"
                  className="block text-sm font-medium text-gray-700"
                >
                  {t("visaType")}
                </label>
                <select
                  id="visaType"
                  value={visaType}
                  onChange={(e) => setVisaType(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Select visa type</option>
                  {VISA_TYPES.map((visa) => (
                    <option key={visa.value} value={visa.value}>
                      {visa.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Visa Expiry Date */}
              <div>
                <label
                  htmlFor="visaExpiry"
                  className="block text-sm font-medium text-gray-700"
                >
                  {t("visaExpiry")}
                </label>
                <input
                  type="date"
                  id="visaExpiry"
                  value={visaExpiry}
                  onChange={(e) => setVisaExpiry(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Priority Date */}
              <div>
                <label
                  htmlFor="priorityDate"
                  className="block text-sm font-medium text-gray-700"
                >
                  {t("priorityDate")}
                </label>
                <input
                  type="date"
                  id="priorityDate"
                  value={priorityDate}
                  onChange={(e) => setPriorityDate(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Subscription Section */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("subscription")}
            </h2>

            <div className="mt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    {t("currentPlan")}
                  </p>
                  <p className="mt-1 text-lg font-semibold capitalize text-gray-900">
                    {profile.subscription.plan}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-sm font-medium ${
                    profile.subscription.plan === "free"
                      ? "bg-gray-100 text-gray-600"
                      : "bg-green-100 text-green-700"
                  }`}
                >
                  {profile.subscription.status}
                </span>
              </div>

              {profile.subscription.plan === "free" ? (
                <Link
                  href="/pricing"
                  className="mt-4 inline-block rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
                >
                  Upgrade to Pro
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={handleManageSubscription}
                  className="mt-4 inline-block rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50"
                >
                  Manage Subscription
                </button>
              )}
            </div>
          </div>

          {/* Account Section */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("account")}
            </h2>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">
                {t("email")}
              </label>
              <input
                type="email"
                value={user.email || ""}
                disabled
                className="mt-1 block w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-2 text-sm text-gray-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Email address cannot be changed
              </p>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:bg-blue-400"
            >
              {isSaving ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  {t("saving")}
                </>
              ) : (
                t("save")
              )}
            </button>

            <button
              type="button"
              onClick={handleSignOut}
              className="text-sm font-medium text-red-600 hover:text-red-700"
            >
              {tNav("signOut")}
            </button>
          </div>
        </form>
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
          <Link
            href="/settings"
            className="flex flex-col items-center p-2 text-xs font-medium text-blue-600"
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
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {tNav("settings")}
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
