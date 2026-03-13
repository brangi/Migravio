"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { FirebaseError } from "firebase/app";
import { Logo } from "@/components/logo";
import { Button } from "@/components/button";
import { Input } from "@/components/input";
import { ArrowRight } from "@/components/icons";

export default function SignupPage() {
  const t = useTranslations("auth");
  const { signUp, signInWithGoogle } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError(t("errors.weakPassword"));
      return;
    }
    if (password.length < 6) {
      setError(t("errors.weakPassword"));
      return;
    }

    setLoading(true);
    try {
      await signUp(email, password);
      router.push("/onboarding");
    } catch (err) {
      if (err instanceof FirebaseError) {
        if (err.code === "auth/email-already-in-use") {
          setError(t("errors.emailInUse"));
        } else if (err.code === "auth/weak-password") {
          setError(t("errors.weakPassword"));
        } else if (err.code === "auth/invalid-email") {
          setError(t("errors.invalidEmail"));
        } else {
          setError(t("errors.generic"));
        }
      } else {
        setError(t("errors.generic"));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    try {
      await signInWithGoogle();
      router.push("/onboarding");
    } catch {
      setError(t("errors.generic"));
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Branded Panel - Hidden on mobile */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary-900 relative overflow-hidden items-center justify-center p-12">
        {/* Decorative Pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg className="absolute top-0 left-0 w-96 h-96" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" className="text-white" d="M44.7,-76.4C58.8,-69.2,71.8,-59.1,79.6,-45.8C87.4,-32.6,90,-16.3,88.5,-0.9C87,14.6,81.4,29.2,73.1,42.8C64.8,56.4,53.8,69,40.1,76.8C26.4,84.6,10,87.6,-5.8,87.2C-21.6,86.8,-36.8,82.9,-50.4,75.3C-64,67.7,-76,56.4,-83.8,42.8C-91.6,29.2,-95.2,13.3,-94.6,-2.8C-94,-18.9,-89.2,-35.2,-80.1,-48.8C-71,-62.4,-57.6,-73.3,-42.8,-80.1C-28,-86.9,-11.8,-89.6,2.4,-93.5C16.6,-97.4,30.6,-83.6,44.7,-76.4Z" transform="translate(100 100)" />
          </svg>
          <svg className="absolute bottom-0 right-0 w-80 h-80" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" className="text-white" d="M39.5,-65.6C51.4,-58.1,61.5,-47.3,68.7,-34.8C75.9,-22.3,80.2,-8.1,79.8,5.9C79.4,19.9,74.3,33.7,66.2,45.8C58.1,57.9,47,68.3,34.1,74.4C21.2,80.5,6.5,82.3,-7.8,80.8C-22.1,79.3,-36,74.5,-48.3,67.9C-60.6,61.3,-71.3,53,-77.8,41.8C-84.3,30.6,-86.6,16.5,-85.4,2.9C-84.2,-10.7,-79.5,-23.8,-72.3,-35.4C-65.1,-47,-55.4,-57.1,-43.5,-64.6C-31.6,-72.1,-17.5,-77,0.1,-77.2C17.7,-77.4,27.6,-73.1,39.5,-65.6Z" transform="translate(100 100)" />
          </svg>
        </div>

        <div className="relative z-10 text-white max-w-md">
          <Logo variant="full" size="lg" />
          <h1 className="mt-8 text-3xl font-[var(--font-display)] leading-tight">
            Start your journey with confidence
          </h1>
          <p className="mt-4 text-primary-100 text-lg">
            Join thousands who trust Migravio for their immigration needs.
          </p>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="flex w-full lg:w-1/2 items-center justify-center bg-surface px-4 py-12">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center">
            <Logo variant="full" size="md" />
          </div>

          <div className="text-center lg:text-left">
            <h2 className="text-2xl font-semibold font-[var(--font-display)] text-text-primary">
              {t("signup")}
            </h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              label={t("email")}
            />

            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              label={t("password")}
            />

            <Input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              label={t("confirmPassword")}
            />

            <Button
              type="submit"
              variant="primary"
              isLoading={loading}
              icon={<ArrowRight />}
              className="w-full"
            >
              {t("emailSignUp")}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-surface px-2 text-text-tertiary">
                {t("orContinueWith")}
              </span>
            </div>
          </div>

          {/* Google button */}
          <button
            onClick={handleGoogle}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-white px-4 py-2.5 text-sm font-medium text-text-primary shadow-sm hover:bg-surface-alt transition-colors"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            {t("googleSignIn")}
          </button>

          <p className="text-center text-sm text-text-secondary">
            {t("hasAccount")}{" "}
            <Link href="/login" className="font-medium text-primary-600 hover:text-primary-700">
              {t("login")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
