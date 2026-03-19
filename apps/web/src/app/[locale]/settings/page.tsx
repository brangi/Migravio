"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { useEffect, useState } from "react";
import { doc, updateDoc, serverTimestamp, Timestamp, collection, addDoc, deleteDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { AppFooter } from "@/components/footer";
import { Button } from "@/components/button";
import { Input } from "@/components/input";
import { DatePicker } from "@/components/date-picker";
import { Save, LogOut, Globe, Plus, X, User, Mail } from "@/components/icons";

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

  // Family member form state
  const [showFamilyForm, setShowFamilyForm] = useState(false);
  const [familyName, setFamilyName] = useState("");
  const [familyRelationship, setFamilyRelationship] = useState("");
  const [familyVisaType, setFamilyVisaType] = useState("");
  const [familyVisaExpiry, setFamilyVisaExpiry] = useState<Date | null>(null);
  const [familyPriorityDate, setFamilyPriorityDate] = useState<Date | null>(null);
  const [isSavingFamily, setIsSavingFamily] = useState(false);

  const isPremium = profile?.subscription?.plan === "premium";

  const RELATIONSHIPS = ["spouse", "child", "parent", "sibling", "other"] as const;

  const resetFamilyForm = () => {
    setFamilyName("");
    setFamilyRelationship("");
    setFamilyVisaType("");
    setFamilyVisaExpiry(null);
    setFamilyPriorityDate(null);
    setShowFamilyForm(false);
  };

  const handleAddFamilyMember = async () => {
    if (!user || !familyName || !familyRelationship) return;
    setIsSavingFamily(true);
    try {
      await addDoc(collection(db, "users", user.uid, "familyMembers"), {
        name: familyName,
        relationship: familyRelationship,
        visaType: familyVisaType,
        visaExpiry: familyVisaExpiry ? Timestamp.fromDate(familyVisaExpiry) : null,
        priorityDate: familyPriorityDate ? Timestamp.fromDate(familyPriorityDate) : null,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });
      resetFamilyForm();
      await refreshProfile();
    } catch (error) {
      console.error("Error adding family member:", error);
    } finally {
      setIsSavingFamily(false);
    }
  };

  const handleDeleteFamilyMember = async (memberId: string) => {
    if (!user || !confirm(t("deleteFamilyConfirm"))) return;
    try {
      await deleteDoc(doc(db, "users", user.uid, "familyMembers", memberId));
      await refreshProfile();
    } catch (error) {
      console.error("Error deleting family member:", error);
    }
  };

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
      alert(t("saveError"));
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
                  placeholder={t("namePlaceholder")}
                  disabled
                  className="mt-2"
                />
                <p className="mt-2 text-xs text-text-tertiary">
                  {t("displayNameHelper")}
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
                  disabled={profile.subscription.plan === "free"}
                  className="mt-2 block w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary shadow-sm transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <option value="en">{t("languages.en")}</option>
                  <option value="es">{t("languages.es")}</option>
                </select>
                {profile.subscription.plan === "free" && (
                  <p className="mt-1.5 text-xs text-primary-600">
                    <Link href="/pricing" className="underline hover:text-primary-700">{t("languageUpgradeHint")}</Link>
                  </p>
                )}
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
                  {profile.subscription.cancelAt ? t("expiresSoon") : profile.subscription.status}
                </span>
              </div>

              {profile.subscription.cancelAt && (
                <p className="mt-3 text-sm text-warning">
                  {t("canceledNotice", {
                    date: new Date(
                      ((profile.subscription.cancelAt.seconds ?? profile.subscription.cancelAt._seconds) || 0) * 1000
                    ).toLocaleDateString(),
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
          <section className="border-b border-border-strong pb-8">
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
                {t("emailHelper")}
              </p>
            </div>
          </section>

          {/* Family Members Section — Premium only */}
          {isPremium && (
            <section className="border-b border-border-strong pb-8">
              <div className="flex items-center justify-between">
                <h2 className="font-[var(--font-display)] text-xl text-text-primary">
                  {t("family")}
                </h2>
                {!showFamilyForm && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setShowFamilyForm(true)}
                    className="inline-flex items-center gap-1 text-sm"
                  >
                    <Plus className="h-4 w-4" />
                    {t("addFamilyMember")}
                  </Button>
                )}
              </div>

              {/* Existing family members list */}
              {profile.familyMembers && profile.familyMembers.length > 0 ? (
                <ul className="mt-4 space-y-3">
                  {profile.familyMembers.map((member) => (
                    <li key={member.id} className="flex items-center gap-3 rounded-lg border border-border p-4">
                      <User className="h-5 w-5 text-text-tertiary" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-text-primary">{member.name}</p>
                        <p className="text-xs text-text-secondary">
                          {t(`relationships.${member.relationship}`)} &middot; {member.visaType || "—"}
                          {member.visaExpiry && (
                            <> &middot; {t("expiryPrefix")} {new Date(member.visaExpiry).toLocaleDateString()}</>
                          )}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteFamilyMember(member.id)}
                        className="text-xs text-danger hover:text-danger/80"
                      >
                        {t("deleteFamilyMember")}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : !showFamilyForm ? (
                <p className="mt-4 text-sm text-text-tertiary">{t("noFamilyMembers")}</p>
              ) : null}

              {/* Add family member form */}
              {showFamilyForm && (
                <div className="mt-4 space-y-4 rounded-lg border border-border p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-text-primary">{t("addFamilyMember")}</h3>
                    <button type="button" onClick={resetFamilyForm} className="text-text-tertiary hover:text-text-primary">
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <Input
                    type="text"
                    value={familyName}
                    onChange={(e) => setFamilyName(e.target.value)}
                    placeholder={t("familyName")}
                  />

                  <select
                    value={familyRelationship}
                    onChange={(e) => setFamilyRelationship(e.target.value)}
                    className="block w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary shadow-sm"
                  >
                    <option value="">{t("relationship")}</option>
                    {RELATIONSHIPS.map((rel) => (
                      <option key={rel} value={rel}>
                        {t(`relationships.${rel}`)}
                      </option>
                    ))}
                  </select>

                  <select
                    value={familyVisaType}
                    onChange={(e) => setFamilyVisaType(e.target.value)}
                    className="block w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary shadow-sm"
                  >
                    <option value="">{t("familyVisaType")}</option>
                    {VISA_TYPES.map((visa) => (
                      <option key={visa.value} value={visa.value}>
                        {tOnboarding(`visaTypes.${visa.value}`)}
                      </option>
                    ))}
                  </select>

                  <DatePicker
                    label={tOnboarding("visaExpiry")}
                    value={familyVisaExpiry}
                    onChange={setFamilyVisaExpiry}
                    placeholder={t("selectDate")}
                  />

                  <DatePicker
                    label={tOnboarding("priorityDate")}
                    value={familyPriorityDate}
                    onChange={setFamilyPriorityDate}
                    placeholder={t("selectDate")}
                  />

                  <Button
                    type="button"
                    variant="primary"
                    disabled={!familyName || !familyRelationship || isSavingFamily}
                    onClick={handleAddFamilyMember}
                    className="w-full"
                  >
                    {isSavingFamily ? t("saving") : t("addFamilyMember")}
                  </Button>
                </div>
              )}
            </section>
          )}

          {/* Support Section — Premium only */}
          {isPremium && (
            <section className="pb-8">
              <h2 className="font-[var(--font-display)] text-xl text-text-primary">
                {t("support")}
              </h2>
              <p className="mt-2 text-sm text-text-secondary">
                {t("supportDescription")}
              </p>
              <a
                href="mailto:support@migravio.ai"
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-3 text-sm font-semibold text-text-primary shadow-sm transition-colors hover:bg-surface-alt"
              >
                <Mail className="h-4 w-4" />
                {t("contactSupport")}
              </a>
            </section>
          )}

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
