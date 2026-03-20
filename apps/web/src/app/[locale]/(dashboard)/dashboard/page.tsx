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
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { AppFooter } from "@/components/footer";
import { Badge } from "@/components/badge";
import { Sparkles, Clock, AlertTriangle, CheckCircle2, ArrowRight, Settings, Lock, Mail, User } from "@/components/icons";

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

  if (diff <= 0) {
    return <Badge variant="danger">{t("expired")}</Badge>;
  }

  const variant = diff > 90 ? "success" : diff > 30 ? "warning" : "danger";
  return <Badge variant={variant}>{t("daysRemaining", { count: diff })}</Badge>;
}

function getActionChecklist(
  visaType: string,
  visaExpiry: Date | null,
  t: (key: string) => string,
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
        text: t("checklist.expired"),
        urgent: true,
      });
    } else if (daysLeft <= 30) {
      items.push({
        id: "expiry-30",
        text: t("checklist.expiry30"),
        urgent: true,
      });
    } else if (daysLeft <= 90) {
      items.push({
        id: "expiry-90",
        text: t("checklist.expiry90"),
        urgent: true,
      });
    } else if (daysLeft <= 180) {
      items.push({
        id: "expiry-180",
        text: t("checklist.expiry180"),
        urgent: false,
      });
    }
  }

  switch (visaType) {
    case "H-1B":
      items.push(
        {
          id: "h1b-1",
          text: t("checklist.h1b1"),
          urgent: false,
        },
        {
          id: "h1b-2",
          text: t("checklist.h1b2"),
          urgent: false,
        },
        {
          id: "h1b-3",
          text: t("checklist.h1b3"),
          urgent: false,
        }
      );
      if (priorityDate) {
        items.push({
          id: "h1b-gc",
          text: t("checklist.h1bVb"),
          urgent: false,
        });
      }
      break;

    case "F-1":
      items.push(
        {
          id: "f1-1",
          text: t("checklist.f1m1"),
          urgent: false,
        },
        {
          id: "f1-2",
          text: t("checklist.f1m2"),
          urgent: false,
        },
        {
          id: "f1-3",
          text: t("checklist.f1m3"),
          urgent: false,
        }
      );
      break;

    case "Family":
      items.push(
        {
          id: "fam-1",
          text: t("checklist.family1"),
          urgent: false,
        },
        {
          id: "fam-2",
          text: t("checklist.family2"),
          urgent: false,
        }
      );
      break;

    case "GreenCard":
      items.push(
        {
          id: "gc-1",
          text: t("checklist.gc1"),
          urgent: false,
        },
        {
          id: "gc-2",
          text: t("checklist.gc2"),
          urgent: false,
        },
        {
          id: "gc-3",
          text: t("checklist.gc3"),
          urgent: false,
        }
      );
      break;

    default:
      items.push({
        id: "default-1",
        text: t("checklist.other"),
        urgent: false,
      });
  }

  return items;
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tNav = useTranslations("nav");
  const { user, profile, loading } = useAuth();
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
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  const isFreeUser = profile.subscription.plan === "free";
  const isPremium = profile.subscription.plan === "premium";

  const checklist = getActionChecklist(
    profile.visaType,
    profile.visaExpiry,
    t,
    profile.priorityDate
  );

  return (
    <div className="flex min-h-screen flex-col bg-surface pb-16 md:pb-0">
      <AppHeader activePage="dashboard" />

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        {/* Profile greeting */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt=""
                className="h-12 w-12 rounded-full border-2 border-primary-100 shadow-sm"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-semibold text-lg">
                {(user.displayName || user.email || "U").charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <h1 className="font-[var(--font-display)] text-2xl font-bold text-text-primary">
                {user.displayName
                  ? t("greeting", { name: user.displayName.split(" ")[0] })
                  : t("title")}
              </h1>
              <p className="text-sm text-text-tertiary">{user.email}</p>
            </div>
          </div>
          <Link
            href="/settings"
            className="hidden md:flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-text-secondary hover:bg-surface-alt transition-colors"
          >
            <Settings className="h-4 w-4" />
            {tNav("settings")}
          </Link>
        </div>

        <div className="mt-6 grid animate-stagger gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Visa Status Card */}
          <div className="rounded-xl border-l-4 border-primary-500 bg-surface-alt p-6 shadow-sm">
            <h2 className="text-sm font-medium text-text-secondary">
              {t("visaStatus")}
            </h2>
            <div className="mt-3 flex items-center justify-between">
              <span className="font-[var(--font-display)] text-lg font-semibold text-text-primary">
                {profile.visaType || "—"}
              </span>
              <DaysRemainingBadge expiryDate={profile.visaExpiry} />
            </div>
            {profile.priorityDate && (
              <p className="mt-2 text-xs text-text-tertiary">
                {t("priorityDateLabel")} {profile.priorityDate.toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Subscription Card */}
          <div className="rounded-xl bg-surface-alt border border-border p-6 shadow-sm">
            <h2 className="text-sm font-medium text-text-secondary">
              {t("subscription")}
            </h2>
            <div className="mt-3 flex items-center justify-between">
              <span className="font-[var(--font-display)] text-lg font-semibold capitalize text-text-primary">
                {profile.subscription.plan}
              </span>
              <Badge variant={profile.subscription.cancelAt ? "warning" : profile.subscription.plan === "free" ? "default" : "success"}>
                {profile.subscription.cancelAt ? t("expiresSoon") : profile.subscription.plan === "free" ? t("freePlan") : t("activePlan")}
              </Badge>
            </div>
            {profile.subscription.plan === "free" ? (
              <Link
                href="/pricing"
                className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                {t("upgradePlan")} <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <button
                onClick={async () => {
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
                  } catch {
                    // Portal not available
                  }
                }}
                className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                {profile.subscription.cancelAt ? t("resubscribe") : t("managePlan")} <ArrowRight className="h-4 w-4" />
              </button>
            )}
            {isPremium && (
              <a
                href="mailto:support@migravio.com"
                className="mt-2 inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
              >
                <Mail className="h-3 w-3" />
                {t("prioritySupport")}
              </a>
            )}
          </div>

          {/* Recent Chats Card */}
          <div className="rounded-xl bg-surface-alt border border-border p-6 shadow-sm">
            <h2 className="text-sm font-medium text-text-secondary">
              {t("recentChats")}
            </h2>
            {recentChats.length === 0 ? (
              <>
                <p className="mt-3 text-sm text-text-tertiary">{t("noChats")}</p>
                <Link
                  href="/chat"
                  className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  {t("startChat")} <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            ) : (
              <ul className="mt-3 space-y-2">
                {recentChats.map((session) => (
                  <li key={session.id}>
                    <Link
                      href={`/chat?session=${session.id}`}
                      className="block rounded-lg p-2 text-sm text-text-primary hover:bg-surface"
                    >
                      <span className="line-clamp-1 font-medium">
                        {session.title}
                      </span>
                      <span className="text-xs text-text-tertiary">
                        {session.updatedAt.toLocaleDateString()}
                      </span>
                    </Link>
                  </li>
                ))}
                <li>
                  <Link
                    href="/chat"
                    className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
                  >
                    {t("startChat")} <ArrowRight className="h-4 w-4" />
                  </Link>
                </li>
              </ul>
            )}
          </div>

          {/* Policy Alerts Card */}
          <div className="relative rounded-xl bg-surface-alt border border-border p-6 shadow-sm overflow-hidden">
            {isFreeUser && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-surface/80 backdrop-blur-sm">
                <Lock className="h-6 w-6 text-text-tertiary" />
                <p className="mt-2 text-sm text-text-secondary">{t("upgradeForAlerts")}</p>
                <Link href="/pricing" className="mt-3 text-sm font-semibold text-primary-600 hover:text-primary-700">{t("upgradeCta")}</Link>
              </div>
            )}
            <h2 className="text-sm font-medium text-text-secondary">
              {t("policyAlerts")}
            </h2>
            {alerts.length === 0 ? (
              <p className="mt-3 text-sm text-text-tertiary">{t("noAlerts")}</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {alerts.slice(0, 3).map((alert) => {
                  const borderColor = alert.affectsVisaTypes.includes(profile.visaType)
                    ? "border-l-accent-500"
                    : "border-l-primary-500";
                  return (
                    <li key={alert.id}>
                      <a
                        href={alert.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`block rounded-lg border border-border border-l-2 ${borderColor} p-3 hover:bg-surface`}
                      >
                        <p className="line-clamp-2 text-sm font-medium text-text-primary">
                          {alert.title}
                        </p>
                        <p className="mt-1 line-clamp-2 text-xs text-text-secondary">
                          {alert.summary}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {alert.affectsVisaTypes.slice(0, 3).map((vt) => (
                            <Badge key={vt} variant="info" className="text-xs">
                              {vt}
                            </Badge>
                          ))}
                          <span className="text-xs text-text-tertiary">
                            {alert.source}
                          </span>
                        </div>
                      </a>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* Action Checklist Card */}
          <div className="relative rounded-xl bg-surface-alt border border-border p-6 shadow-sm md:col-span-2 lg:col-span-3 overflow-hidden">
            {isFreeUser && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-surface/80 backdrop-blur-sm">
                <Lock className="h-6 w-6 text-text-tertiary" />
                <p className="mt-2 text-sm text-text-secondary">{t("upgradeForChecklist")}</p>
                <Link href="/pricing" className="mt-3 text-sm font-semibold text-primary-600 hover:text-primary-700">{t("upgradeCta")}</Link>
              </div>
            )}
            <h2 className="text-sm font-medium text-text-secondary">
              {t("actionChecklist")}
            </h2>
            {checklist.length === 0 ? (
              <p className="mt-3 text-sm text-text-tertiary">
                {t("checklist.noItems")}
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {checklist.map((item) => (
                  <li key={item.id} className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs border-2 ${
                        item.urgent
                          ? "border-danger bg-danger/10 text-danger"
                          : "border-success bg-success/10 text-success"
                      }`}
                    >
                      {item.urgent ? <AlertTriangle className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
                    </span>
                    <span
                      className={`text-sm ${
                        item.urgent
                          ? "font-medium text-danger"
                          : "text-text-primary"
                      }`}
                    >
                      {item.text}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Family Members Card */}
          <div className="relative rounded-xl bg-surface-alt border border-border p-6 shadow-sm overflow-hidden">
            {!isPremium && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-surface/80 backdrop-blur-sm">
                <Lock className="h-6 w-6 text-text-tertiary" />
                <p className="mt-2 text-sm text-text-secondary">{t("upgradeForFamily")}</p>
                <Link href="/pricing" className="mt-3 text-sm font-semibold text-primary-600 hover:text-primary-700">
                  {profile.subscription.plan === "free" ? t("upgradeCta") : t("upgradeToPremium")}
                </Link>
              </div>
            )}
            <h2 className="text-sm font-medium text-text-secondary">
              {t("familyMembers")}
            </h2>
            {isPremium && profile.familyMembers && profile.familyMembers.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {profile.familyMembers.map((member) => (
                  <li key={member.id} className="flex items-center gap-3 rounded-lg border border-border p-3">
                    <User className="h-5 w-5 text-text-tertiary" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-text-primary">{member.name}</p>
                      <p className="text-xs text-text-secondary">{member.relationship} &middot; {member.visaType}</p>
                    </div>
                    {member.visaExpiry && <DaysRemainingBadge expiryDate={new Date(member.visaExpiry)} />}
                  </li>
                ))}
                <li>
                  <Link href="/settings" className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700">
                    {t("addFamilyMember")} <ArrowRight className="h-4 w-4" />
                  </Link>
                </li>
              </ul>
            ) : isPremium ? (
              <div className="mt-3">
                <p className="text-sm text-text-tertiary">{t("noFamilyMembersYet")}</p>
                <Link href="/settings" className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700">
                  {t("addFamilyMember")} <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ) : (
              <p className="mt-3 text-sm text-text-tertiary">{t("familyDescription")}</p>
            )}
          </div>
        </div>

        {/* Attorney CTA */}
        <div className="mt-8">
          <Link
            href="/attorneys"
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-primary-700"
          >
            <Sparkles className="h-4 w-4" />
            {t("talkToAttorney")}
          </Link>
        </div>
      </main>

      <MobileNav activePage="dashboard" />
      <AppFooter />
    </div>
  );
}
