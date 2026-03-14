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
            {t("brandedPanel.signupHeadline")}
          </h1>
          <p className="mt-4 text-primary-200 text-lg">
            {t("brandedPanel.signupSubtext")}
          </p>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="flex w-full lg:w-1/2 items-center justify-center bg-surface px-4 py-12">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center">
            <Link href="/" className="inline-block hover:opacity-80 transition-opacity">
              <Logo variant="full" size="md" />
            </Link>
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
