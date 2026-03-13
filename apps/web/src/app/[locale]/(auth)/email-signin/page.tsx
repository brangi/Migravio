"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { useRouter, Link } from "@/i18n/navigation";

export default function EmailSignInPage() {
  const t = useTranslations("auth");
  const { completeMagicLinkSignIn, profile } = useAuth();
  const router = useRouter();
  const [error, setError] = useState(false);
  const [completing, setCompleting] = useState(true);

  useEffect(() => {
    const complete = async () => {
      try {
        const success = await completeMagicLinkSignIn(window.location.href);
        if (success) {
          // Give auth state a moment to propagate, then redirect
          setTimeout(() => {
            if (profile && profile.onboardingComplete) {
              router.push("/dashboard");
            } else {
              router.push("/onboarding");
            }
          }, 500);
        } else {
          setError(true);
          setCompleting(false);
        }
      } catch {
        setError(true);
        setCompleting(false);
      }
    };
    complete();
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-sm text-gray-600">{t("magicLinkError")}</p>
          <Link
            href="/login"
            className="inline-block text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            {t("backToLogin")}
          </Link>
        </div>
      </div>
    );
  }

  if (completing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <div className="h-8 w-8 mx-auto animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          <p className="text-sm text-gray-600">{t("magicLinkCompleting")}</p>
        </div>
      </div>
    );
  }

  return null;
}
