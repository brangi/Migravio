"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "@/i18n/navigation";
import { doc, updateDoc, serverTimestamp, Timestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";

const VISA_TYPES = ["H-1B", "F-1", "Family", "GreenCard", "Other"] as const;

export default function OnboardingPage() {
  const t = useTranslations("onboarding");
  const tCommon = useTranslations("common");
  const { user, refreshProfile } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [language, setLanguage] = useState("en");
  const [visaType, setVisaType] = useState("");
  const [visaExpiry, setVisaExpiry] = useState("");
  const [priorityDate, setPriorityDate] = useState("");
  const [saving, setSaving] = useState(false);

  const handleComplete = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await updateDoc(doc(db, "users", user.uid), {
        language,
        visaType,
        visaExpiry: visaExpiry ? Timestamp.fromDate(new Date(visaExpiry)) : null,
        priorityDate: priorityDate
          ? Timestamp.fromDate(new Date(priorityDate))
          : null,
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
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-blue-700">
            {t("welcome")}
          </h1>
          {/* Progress indicator */}
          <div className="mt-6 flex justify-center gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 w-16 rounded-full ${
                  s <= step ? "bg-blue-600" : "bg-gray-200"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step 1: Language */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("step1Title")}
            </h2>
            <p className="text-sm text-gray-600">{t("step1Subtitle")}</p>
            <div className="space-y-2">
              {[
                { code: "en", label: "English" },
                { code: "es", label: "Espanol" },
              ].map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`flex w-full items-center rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                    language === lang.code
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              {tCommon("next")}
            </button>
          </div>
        )}

        {/* Step 2: Visa Type */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("step2Title")}
            </h2>
            <p className="text-sm text-gray-600">{t("step2Subtitle")}</p>
            <div className="space-y-2">
              {VISA_TYPES.map((vt) => (
                <button
                  key={vt}
                  onClick={() => setVisaType(vt)}
                  className={`flex w-full items-center rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                    visaType === vt
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {t(`visaTypes.${vt}`)}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                {tCommon("back")}
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!visaType}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {tCommon("next")}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Dates */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {t("step3Title")}
            </h2>
            <p className="text-sm text-gray-600">{t("step3Subtitle")}</p>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t("visaExpiry")}
              </label>
              <input
                type="date"
                value={visaExpiry}
                onChange={(e) => setVisaExpiry(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t("priorityDate")}
              </label>
              <input
                type="date"
                value={priorityDate}
                onChange={(e) => setPriorityDate(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(2)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                {tCommon("back")}
              </button>
              <button
                onClick={handleComplete}
                disabled={saving}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "..." : tCommon("getStarted")}
              </button>
            </div>

            <button
              onClick={handleComplete}
              disabled={saving}
              className="w-full text-center text-sm text-gray-500 hover:text-gray-700"
            >
              {t("skip")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
