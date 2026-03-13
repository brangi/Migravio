"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import {
  collection,
  query,
  orderBy,
  limit,
  getDocs,
  where,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import LanguageSwitcher from "@/components/language-switcher";

interface ChatSession {
  id: string;
  title: string;
  updatedAt: Date;
}

interface PolicyAlert {
  id: string;
  title: string;
  summary: string;
  source: string;
  sourceUrl: string;
  affectsVisaTypes: string[];
  publishedAt: string;
}

interface ChecklistItem {
  id: string;
  text: string;
  urgent: boolean;
}

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

function getActionChecklist(
  visaType: string,
  visaExpiry: Date | null,
  priorityDate: Date | null
): ChecklistItem[] {
  const items: ChecklistItem[] = [];
  const now = new Date();

  if (visaExpiry) {
    const daysLeft = Math.ceil(
      (visaExpiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysLeft < 0) {
      items.push({
        id: "expired",
        text: "Your visa has expired. Consult an immigration attorney immediately.",
        urgent: true,
      });
    } else if (daysLeft <= 30) {
      items.push({
        id: "expiry-30",
        text: "Your visa expires in less than 30 days. Take action now.",
        urgent: true,
      });
    } else if (daysLeft <= 90) {
      items.push({
        id: "expiry-90",
        text: "Your visa expires in less than 90 days. Start your renewal process.",
        urgent: true,
      });
    } else if (daysLeft <= 180) {
      items.push({
        id: "expiry-180",
        text: "Consider starting your renewal paperwork soon (visa expires in ~6 months).",
        urgent: false,
      });
    }
  }

  switch (visaType) {
    case "H-1B":
      items.push(
        {
          id: "h1b-1",
          text: "Keep I-797 approval notice in a safe place",
          urgent: false,
        },
        {
          id: "h1b-2",
          text: "Verify your employer is maintaining your H-1B status",
          urgent: false,
        },
        {
          id: "h1b-3",
          text: "Track your 6-year H-1B limit and plan for extensions or green card",
          urgent: false,
        }
      );
      if (priorityDate) {
        items.push({
          id: "h1b-gc",
          text: "Check the monthly Visa Bulletin for your priority date progress",
          urgent: false,
        });
      }
      break;

    case "F-1":
      items.push(
        {
          id: "f1-1",
          text: "Maintain full-time enrollment to keep F-1 status",
          urgent: false,
        },
        {
          id: "f1-2",
          text: "Apply for OPT/CPT before your program end date",
          urgent: false,
        },
        {
          id: "f1-3",
          text: "Keep your I-20 updated with your DSO",
          urgent: false,
        }
      );
      break;

    case "Family":
      items.push(
        {
          id: "fam-1",
          text: "Gather supporting documents (proof of relationship, financial affidavit)",
          urgent: false,
        },
        {
          id: "fam-2",
          text: "Check Visa Bulletin for your priority date category",
          urgent: false,
        }
      );
      break;

    case "GreenCard":
      items.push(
        {
          id: "gc-1",
          text: "Maintain your permanent resident status (don't travel abroad for 6+ months without re-entry permit)",
          urgent: false,
        },
        {
          id: "gc-2",
          text: "Renew your green card (Form I-90) before it expires",
          urgent: false,
        },
        {
          id: "gc-3",
          text: "Consider applying for naturalization if eligible (5 years as LPR, or 3 years if married to US citizen)",
          urgent: false,
        }
      );
      break;

    default:
      items.push({
        id: "default-1",
        text: "Update your visa type in settings for personalized action items",
        urgent: false,
      });
  }

  return items;
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const { user, profile, loading, signOut } = useAuth();
  const router = useRouter();

  const [recentChats, setRecentChats] = useState<ChatSession[]>([]);
  const [alerts, setAlerts] = useState<PolicyAlert[]>([]);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && profile && !profile.onboardingComplete) {
      router.push("/onboarding");
    }
  }, [loading, user, profile, router]);

  // Load recent chat sessions
  useEffect(() => {
    if (!user) return;

    const loadChats = async () => {
      try {
        const sessionsRef = collection(
          db,
          "users",
          user.uid,
          "chatSessions"
        );
        const q = query(sessionsRef, orderBy("updatedAt", "desc"), limit(5));
        const snap = await getDocs(q);
        const sessions: ChatSession[] = [];
        snap.forEach((doc) => {
          const data = doc.data();
          sessions.push({
            id: doc.id,
            title: data.title || "Untitled",
            updatedAt: data.updatedAt?.toDate() || new Date(),
          });
        });
        setRecentChats(sessions);
      } catch {
        // Firestore not available or no sessions yet
      }
    };

    loadChats();
  }, [user]);

  // Load policy alerts filtered by visa type
  useEffect(() => {
    if (!user || !profile?.visaType) return;

    const loadAlerts = async () => {
      try {
        const alertsRef = collection(db, "policyAlerts");
        const q = query(
          alertsRef,
          where("active", "==", true),
          orderBy("scrapedAt", "desc"),
          limit(5)
        );
        const snap = await getDocs(q);
        const items: PolicyAlert[] = [];
        snap.forEach((doc) => {
          const data = doc.data();
          // Client-side filter by visa type (includes "General" alerts for everyone)
          const affects = data.affectsVisaTypes || ["General"];
          if (
            affects.includes("General") ||
            affects.includes(profile.visaType)
          ) {
            items.push({
              id: doc.id,
              title: data.title || "",
              summary: data.aiSummary || data.summary || "",
              source: data.source || "",
              sourceUrl: data.sourceUrl || "",
              affectsVisaTypes: affects,
              publishedAt: data.publishedAt || "",
            });
          }
        });
        setAlerts(items);
      } catch {
        // Alerts collection may not exist yet
      }
    };

    loadAlerts();
  }, [user, profile?.visaType]);

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const checklist = getActionChecklist(
    profile.visaType,
    profile.visaExpiry,
    profile.priorityDate
  );

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 pb-16 md:pb-0">
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
                {profile.visaType || "\u2014"}
              </span>
              <DaysRemainingBadge expiryDate={profile.visaExpiry} />
            </div>
            {profile.priorityDate && (
              <p className="mt-2 text-xs text-gray-400">
                Priority date: {profile.priorityDate.toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Subscription Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("subscription")}
            </h2>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-lg font-semibold capitalize text-gray-900">
                {profile.subscription.plan}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  profile.subscription.plan === "free"
                    ? "bg-gray-100 text-gray-600"
                    : "bg-green-100 text-green-700"
                }`}
              >
                {profile.subscription.plan === "free" ? t("freePlan") : t("activePlan")}
              </span>
            </div>
            {profile.subscription.plan === "free" ? (
              <Link
                href="/pricing"
                className="mt-3 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                {t("upgradePlan")} &rarr;
              </Link>
            ) : (
              <button
                onClick={async () => {
                  try {
                    const res = await fetch("/api/stripe/portal", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        customerId: (profile as unknown as Record<string, unknown>)?.stripeCustomerId,
                        locale: profile.language,
                      }),
                    });
                    const { url } = await res.json();
                    if (url) window.location.href = url;
                  } catch {
                    // Portal not available
                  }
                }}
                className="mt-3 text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                {t("managePlan")} &rarr;
              </button>
            )}
          </div>

          {/* Recent Chats Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("recentChats")}
            </h2>
            {recentChats.length === 0 ? (
              <>
                <p className="mt-3 text-sm text-gray-400">{t("noChats")}</p>
                <Link
                  href="/chat"
                  className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  {t("startChat")} &rarr;
                </Link>
              </>
            ) : (
              <ul className="mt-3 space-y-2">
                {recentChats.map((session) => (
                  <li key={session.id}>
                    <Link
                      href={`/chat?session=${session.id}`}
                      className="block rounded-lg p-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <span className="line-clamp-1 font-medium">
                        {session.title}
                      </span>
                      <span className="text-xs text-gray-400">
                        {session.updatedAt.toLocaleDateString()}
                      </span>
                    </Link>
                  </li>
                ))}
                <li>
                  <Link
                    href="/chat"
                    className="mt-1 inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
                  >
                    {t("startChat")} &rarr;
                  </Link>
                </li>
              </ul>
            )}
          </div>

          {/* Policy Alerts Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-medium text-gray-500">
              {t("policyAlerts")}
            </h2>
            {alerts.length === 0 ? (
              <p className="mt-3 text-sm text-gray-400">{t("noAlerts")}</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {alerts.slice(0, 3).map((alert) => (
                  <li key={alert.id}>
                    <a
                      href={alert.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border border-gray-100 p-3 hover:bg-gray-50"
                    >
                      <p className="line-clamp-2 text-sm font-medium text-gray-800">
                        {alert.title}
                      </p>
                      <p className="mt-1 line-clamp-2 text-xs text-gray-500">
                        {alert.summary}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {alert.affectsVisaTypes.slice(0, 3).map((vt) => (
                          <span
                            key={vt}
                            className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-600"
                          >
                            {vt}
                          </span>
                        ))}
                        <span className="text-xs text-gray-400">
                          {alert.source}
                        </span>
                      </div>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Action Checklist Card */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:col-span-2 lg:col-span-3">
            <h2 className="text-sm font-medium text-gray-500">
              {t("actionChecklist")}
            </h2>
            {checklist.length === 0 ? (
              <p className="mt-3 text-sm text-gray-400">
                No action items right now.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {checklist.map((item) => (
                  <li key={item.id} className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs ${
                        item.urgent
                          ? "bg-red-100 text-red-600"
                          : "bg-gray-100 text-gray-400"
                      }`}
                    >
                      {item.urgent ? "!" : "\u2713"}
                    </span>
                    <span
                      className={`text-sm ${
                        item.urgent
                          ? "font-medium text-red-700"
                          : "text-gray-700"
                      }`}
                    >
                      {item.text}
                    </span>
                  </li>
                ))}
              </ul>
            )}
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
          <Link
            href="/settings"
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
