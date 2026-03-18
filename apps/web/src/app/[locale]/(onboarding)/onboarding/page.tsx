"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "@/i18n/navigation";
import { doc, updateDoc, serverTimestamp, Timestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { Logo } from "@/components/logo";
import { Button } from "@/components/button";
import { DatePicker } from "@/components/date-picker";
import { Check, Globe } from "@/components/icons";

const VISA_TYPES = ["H-1B", "F-1", "Family", "GreenCard", "Other"] as const;

const LANGUAGE_OPTIONS = [
  { code: "en", label: "English", flag: "🇺🇸" },
  { code: "es", label: "Español", flag: "🇪🇸" },
];

export default function OnboardingPage() {
  const t = useTranslations("onboarding");
  const tCommon = useTranslations("common");
  const { user, refreshProfile } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [language, setLanguage] = useState("en");
  const [visaType, setVisaType] = useState("");
  const [visaExpiry, setVisaExpiry] = useState<Date | null>(null);
  const [priorityDate, setPriorityDate] = useState<Date | null>(null);
  const [saving, setSaving] = useState(false);

  const totalSteps = 3;

  const handleComplete = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await updateDoc(doc(db, "users", user.uid), {
        language,
        visaType,
        visaExpiry: visaExpiry ? Timestamp.fromDate(visaExpiry) : null,
        priorityDate: priorityDate ? Timestamp.fromDate(priorityDate) : null,
        onboardingComplete: true,
        updatedAt: serverTimestamp(),
      });
      await refreshProfile();
      router.push("/dashboard");
    } catch (err) {
      console.error("Failed to save onboarding:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-lg space-y-8">
        {/* Logo */}
        <div className="text-center">
          <Logo className="mx-auto h-10" />
        </div>

        {/* Progress Section */}
        <div className="space-y-4">
          {/* Step Labels */}
          <div className="flex justify-between text-xs font-medium text-text-tertiary">
            <span className={step >= 1 ? "text-primary-600" : ""}>
              Step 1
            </span>
            <span className={step >= 2 ? "text-primary-600" : ""}>
              Step 2
            </span>
            <span className={step >= 3 ? "text-primary-600" : ""}>
              Step 3
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-2 overflow-hidden rounded-full bg-primary-100">
            <div
              className="h-full bg-primary-600 transition-all duration-300 ease-out"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Welcome Header */}
        <div className="text-center">
          <h1 className="font-[var(--font-display)] text-3xl text-text-primary">
            {t("welcome")}
          </h1>
        </div>

        {/* Step 1: Language */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="font-[var(--font-display)] text-xl text-text-primary">
                {t("step1Title")}
              </h2>
              <p className="text-sm text-text-secondary">{t("step1Subtitle")}</p>
            </div>

            <div className="space-y-3">
              {LANGUAGE_OPTIONS.map((lang) => {
                const isLocked = lang.code !== "en";
                return (
                  <button
                    key={lang.code}
                    onClick={() => !isLocked && setLanguage(lang.code)}
                    disabled={isLocked}
                    className={`group relative flex w-full items-center justify-between rounded-xl border-2 px-6 py-4 text-left transition-all duration-200 ${
                      isLocked
                        ? "border-border bg-surface-alt opacity-60 cursor-not-allowed"
                        : language === lang.code
                          ? "border-primary-600 bg-primary-50 shadow-sm"
                          : "border-border bg-surface hover:border-primary-300 hover:bg-surface-alt"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{lang.flag}</span>
                      <div>
                        <span
                          className={`text-base font-medium ${
                            isLocked
                              ? "text-text-tertiary"
                              : language === lang.code
                                ? "text-primary-700"
                                : "text-text-primary"
                          }`}
                        >
                          {lang.label}
                        </span>
                        {isLocked && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700">
                            Pro
                          </span>
                        )}
                      </div>
                    </div>
                    {!isLocked && language === lang.code && (
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-600">
                        <Check className="h-4 w-4 text-white" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            <Button
              onClick={() => setStep(2)}
              variant="primary"
              className="w-full"
            >
              {tCommon("next")}
            </Button>
          </div>
        )}

        {/* Step 2: Visa Type */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="font-[var(--font-display)] text-xl text-text-primary">
                {t("step2Title")}
              </h2>
              <p className="text-sm text-text-secondary">{t("step2Subtitle")}</p>
            </div>

            <div className="space-y-3">
              {VISA_TYPES.map((vt) => (
                <button
                  key={vt}
                  onClick={() => setVisaType(vt)}
                  className={`group relative flex w-full items-center justify-between rounded-xl border-2 px-6 py-4 text-left transition-all duration-200 ${
                    visaType === vt
                      ? "border-primary-600 bg-primary-50 shadow-sm"
                      : "border-border bg-surface hover:border-primary-300 hover:bg-surface-alt"
                  }`}
                >
                  <span
                    className={`text-base font-medium ${
                      visaType === vt
                        ? "text-primary-700"
                        : "text-text-primary"
                    }`}
                  >
                    {t(`visaTypes.${vt}`)}
                  </span>
                  {visaType === vt && (
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-600">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                  )}
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <Button
                onClick={() => setStep(1)}
                variant="secondary"
                className="flex-1"
              >
                {tCommon("back")}
              </Button>
              <Button
                onClick={() => setStep(3)}
                disabled={!visaType}
                variant="primary"
                className="flex-1"
              >
                {tCommon("next")}
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Dates */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="font-[var(--font-display)] text-xl text-text-primary">
                {t("step3Title")}
              </h2>
              <p className="text-sm text-text-secondary">{t("step3Subtitle")}</p>
            </div>

            <div className="space-y-5">
              <DatePicker
                label={t("visaExpiry")}
                value={visaExpiry}
                onChange={setVisaExpiry}
                placeholder={t("selectDate")}
                helperText={t("visaExpiryHelper")}
              />

              <DatePicker
                label={t("priorityDate")}
                value={priorityDate}
                onChange={setPriorityDate}
                placeholder={t("selectDate")}
                helperText={t("priorityDateHelper")}
              />
            </div>

            <div className="flex gap-3">
              <Button
                onClick={() => setStep(2)}
                variant="secondary"
                className="flex-1"
              >
                {tCommon("back")}
              </Button>
              <Button
                onClick={handleComplete}
                disabled={saving}
                variant="primary"
                className="flex-1"
              >
                {saving ? (
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Saving...</span>
                  </div>
                ) : (
                  tCommon("getStarted")
                )}
              </Button>
            </div>

            <Button
              onClick={handleComplete}
              disabled={saving}
              variant="ghost"
              className="w-full"
            >
              {t("skip")}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
