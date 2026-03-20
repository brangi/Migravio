"use client";

import { useEffect, useState, useRef } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { useRouter, Link } from "@/i18n/navigation";
import { Logo } from "@/components/logo";
import { AlertTriangle } from "@/components/icons";
import { doc, getDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";

export default function EmailSignInPage() {
  const t = useTranslations("auth");
  const { completeMagicLinkSignIn } = useAuth();
  const router = useRouter();
  const [error, setError] = useState(false);
  const [completing, setCompleting] = useState(true);
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    const complete = async () => {
      try {
        const success = await completeMagicLinkSignIn(window.location.href);
        if (success) {
          // completeMagicLinkSignIn returns the signed-in user via auth state,
          // but profile may not be loaded yet. Fetch directly from Firestore.
          const { getAuth } = await import("firebase/auth");
          const currentUser = getAuth().currentUser;
          if (currentUser) {
            const userDoc = await getDoc(doc(db, "users", currentUser.uid));
            if (userDoc.exists() && userDoc.data().onboardingComplete) {
              router.push("/dashboard");
            } else {
              router.push("/onboarding");
            }
          } else {
            router.push("/onboarding");
          }
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
      <div className="flex min-h-screen">
        {/* Left Branded Panel - Hidden on mobile */}
        <div className="hidden lg:flex lg:w-1/2 bg-primary-900 relative overflow-hidden items-center justify-center p-12">
          {/* Decorative Pattern */}
          <div className="absolute inset-0">
            <div className="absolute -top-20 -left-20 w-96 h-96 rounded-full bg-primary-700/20" />
            <div className="absolute -bottom-32 -right-20 w-80 h-80 rounded-full bg-primary-700/20" />
            <div className="absolute top-1/3 right-1/4 w-32 h-32 rounded-full bg-accent-500/10" />
          </div>

          <div className="relative z-10 max-w-md">
            <Link href="/" className="inline-block hover:opacity-80 transition-opacity">
              <Logo variant="full" size="lg" colorScheme="dark" />
            </Link>
            <h1 className="mt-8 text-3xl font-[var(--font-display)] leading-tight text-white">
              {t("brandedPanel.emailSigninErrorHeadline")}
            </h1>
            <p className="mt-4 text-primary-200 text-lg">
              {t("brandedPanel.emailSigninErrorSubtext")}
            </p>
          </div>
        </div>

        {/* Right Error Panel */}
        <div className="flex w-full lg:w-1/2 items-center justify-center bg-surface px-4 py-12">
          <div className="w-full max-w-md space-y-6 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold font-[var(--font-display)] text-text-primary">
              {t("brandedPanel.unableToSignIn")}
            </h2>
            <p className="text-base text-text-secondary">
              {t("magicLinkError")}
            </p>
            <Link
              href="/login"
              className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              {t("backToLogin")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (completing) {
    return (
      <div className="flex min-h-screen">
        {/* Left Branded Panel - Hidden on mobile */}
        <div className="hidden lg:flex lg:w-1/2 bg-primary-900 relative overflow-hidden items-center justify-center p-12">
          {/* Decorative Pattern */}
          <div className="absolute inset-0">
            <div className="absolute -top-20 -left-20 w-96 h-96 rounded-full bg-primary-700/20" />
            <div className="absolute -bottom-32 -right-20 w-80 h-80 rounded-full bg-primary-700/20" />
            <div className="absolute top-1/3 right-1/4 w-32 h-32 rounded-full bg-accent-500/10" />
          </div>

          <div className="relative z-10 max-w-md">
            <Link href="/" className="inline-block hover:opacity-80 transition-opacity">
              <Logo variant="full" size="lg" colorScheme="dark" />
            </Link>
            <h1 className="mt-8 text-3xl font-[var(--font-display)] leading-tight text-white">
              {t("brandedPanel.emailSigninHeadline")}
            </h1>
            <p className="mt-4 text-primary-200 text-lg">
              {t("brandedPanel.emailSigninSubtext")}
            </p>
          </div>
        </div>

        {/* Right Loading Panel */}
        <div className="flex w-full lg:w-1/2 items-center justify-center bg-surface px-4 py-12">
          <div className="w-full max-w-md space-y-6 text-center">
            <div className="h-12 w-12 mx-auto animate-spin rounded-full border-4 border-primary-600 border-t-transparent" />
            <p className="text-base text-text-secondary">
              {t("magicLinkCompleting")}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
