"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link } from "@/i18n/navigation";
import { useRouter } from "@/i18n/navigation";
import { useEffect } from "react";

function DaysRemainingBadge({ expiryDate }: { expiryDate: Date | null }) {
  const t = useTranslations("dashboard");

  if (!expiryDate) return null;

  const now = new Date();
  const diff = Math.ceil(
    (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (diff < 0) {
    return (
      <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
        {t("expired")}
      </span>
    );
  }

  const color =
    diff > 90
      ? "bg-green-100 text-green-700"
      : diff > 30
        ? "bg-yellow-100 text-yellow-700"
        : "bg-red-100 text-red-700";

  return (
    <span className={`rounded-full px-3 py-1 text-sm font-medium ${color}`}>
      {t("daysRemaining", { count: diff })}
    </span>
  );
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const { user, profile, loading, signOut } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && profile && !profile.onboardingComplete) {
      router.push("/onboarding");
    }
  }, [loading, user, profile, router]);

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <span className="text-xl font-bold text-blue-700">Migravio</span>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-blue-600"
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
          <button
            onClick={signOut}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {tNav("signOut")}
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">{t("title")}</h1>

        <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Visa Status Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("visaStatus")}
            </h2>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-lg font-semibold text-gray-900">
                {profile.visaType || "—"}
              </span>
              <DaysRemainingBadge expiryDate={profile.visaExpiry} />
            </div>
          </div>

          {/* Recent Chats Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("recentChats")}
            </h2>
            <p className="mt-3 text-sm text-gray-400">{t("noChats")}</p>
            <Link
              href="/chat"
              className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              {t("startChat")} &rarr;
            </Link>
          </div>

          {/* Policy Alerts Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("policyAlerts")}
            </h2>
            <p className="mt-3 text-sm text-gray-400">{t("noAlerts")}</p>
          </div>

          {/* Action Checklist Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:col-span-2 lg:col-span-3">
            <h2 className="text-sm font-medium text-gray-500">
              {t("actionChecklist")}
            </h2>
            <div className="mt-3 text-sm text-gray-400">
              Coming soon — personalized action items based on your visa type
              and dates.
            </div>
          </div>
        </div>

        {/* Attorney CTA */}
        <div className="mt-8">
          <Link
            href="/attorneys"
            className="inline-flex items-center rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
          >
            {t("talkToAttorney")}
          </Link>
        </div>
      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white md:hidden">
        <div className="flex justify-around py-2">
          <Link
            href="/dashboard"
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
