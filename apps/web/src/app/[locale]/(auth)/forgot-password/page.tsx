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
              We'll help you get back on track
            </h1>
            <p className="mt-4 text-primary-100 text-lg">
              Check your email for a secure password reset link.
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
            Reset your password securely
          </h1>
          <p className="mt-4 text-primary-100 text-lg">
            Enter your email and we'll send you a reset link.
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
