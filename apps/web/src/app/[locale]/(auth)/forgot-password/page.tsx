"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link } from "@/i18n/navigation";
import { FirebaseError } from "firebase/app";
import { Logo } from "@/components/logo";
import { Button } from "@/components/button";
import { Input } from "@/components/input";
import { Mail, ArrowRight } from "@/components/icons";

export default function ForgotPasswordPage() {
  const t = useTranslations("auth");
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch (err) {
      if (err instanceof FirebaseError && err.code === "auth/invalid-email") {
        setError(t("errors.invalidEmail"));
      } else {
        setError(t("errors.generic"));
      }
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
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
              {t("brandedPanel.forgotSentHeadline")}
            </h1>
            <p className="mt-4 text-primary-200 text-lg">
              {t("brandedPanel.forgotSentSubtext")}
            </p>
          </div>
        </div>

        {/* Right Success Panel */}
        <div className="flex w-full lg:w-1/2 items-center justify-center bg-surface px-4 py-12">
          <div className="w-full max-w-md space-y-6 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
              <Mail className="h-8 w-8 text-primary-600" />
            </div>
            <h2 className="text-xl font-semibold font-[var(--font-display)] text-text-primary">
              {t("forgotPasswordSent")}
            </h2>
            <p className="text-sm text-text-secondary">
              {t("forgotPasswordSentDescription", { email })}
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
          <Logo variant="full" size="lg" colorScheme="dark" />
          <h1 className="mt-8 text-3xl font-[var(--font-display)] leading-tight text-white">
            {t("brandedPanel.forgotHeadline")}
          </h1>
          <p className="mt-4 text-primary-200 text-lg">
            {t("brandedPanel.forgotSubtext")}
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
              {t("forgotPasswordTitle")}
            </h2>
            <p className="mt-2 text-sm text-text-secondary">
              {t("forgotPasswordDescription")}
            </p>
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

            <Button
              type="submit"
              variant="primary"
              isLoading={loading}
              icon={<ArrowRight />}
              className="w-full"
            >
              {t("forgotPasswordSend")}
            </Button>
          </form>

          <p className="text-center">
            <Link href="/login" className="text-sm font-medium text-primary-600 hover:text-primary-700">
              {t("backToLogin")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
