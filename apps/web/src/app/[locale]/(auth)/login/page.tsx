"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link, useRouter } from "@/i18n/navigation";
import { FirebaseError } from "firebase/app";
import { Logo } from "@/components/logo";
import { Button } from "@/components/button";
import { Input } from "@/components/input";
import { Mail, ArrowRight } from "@/components/icons";

type AuthTab = "magic-link" | "password";

export default function LoginPage() {
  const t = useTranslations("auth");
  const { signIn, signInWithGoogle, sendMagicLink } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<AuthTab>("magic-link");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signIn(email, password);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof FirebaseError) {
        if (
          err.code === "auth/wrong-password" ||
          err.code === "auth/user-not-found" ||
          err.code === "auth/invalid-credential"
        ) {
          setError(t("errors.wrongPassword"));
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

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await sendMagicLink(email);
      setMagicLinkSent(true);
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

  const handleGoogle = async () => {
    setError("");
    try {
      await signInWithGoogle();
      router.push("/dashboard");
    } catch {
      setError(t("errors.generic"));
    }
  };

  if (magicLinkSent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
            <Mail className="h-8 w-8 text-primary-600" />
          </div>
          <h2 className="text-xl font-semibold font-[var(--font-display)] text-text-primary">
            {t("magicLinkSent")}
          </h2>
          <p className="text-sm text-text-secondary">
            {t("magicLinkSentDescription", { email })}
          </p>
          <button
            onClick={() => { setMagicLinkSent(false); setEmail(""); }}
            className="text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            {t("backToLogin")}
          </button>
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
          <Link href="/" className="inline-block hover:opacity-80 transition-opacity">
            <Logo variant="full" size="lg" colorScheme="dark" />
          </Link>
          <h1 className="mt-8 text-3xl font-[var(--font-display)] leading-tight text-white">
            {t("brandedPanel.loginHeadline")}
          </h1>
          <p className="mt-4 text-primary-200 text-lg">
            {t("brandedPanel.loginSubtext")}
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
              {t("login")}
            </h2>
          </div>

          {/* Tab selector with underline style */}
          <div className="border-b border-border">
            <div className="flex gap-8">
              <button
                onClick={() => { setTab("magic-link"); setError(""); }}
                className={`pb-3 text-sm font-medium transition-colors relative ${
                  tab === "magic-link"
                    ? "text-primary-600"
                    : "text-text-tertiary hover:text-text-secondary"
                }`}
              >
                {t("tabMagicLink")}
                {tab === "magic-link" && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
                )}
              </button>
              <button
                onClick={() => { setTab("password"); setError(""); }}
                className={`pb-3 text-sm font-medium transition-colors relative ${
                  tab === "password"
                    ? "text-primary-600"
                    : "text-text-tertiary hover:text-text-secondary"
                }`}
              >
                {t("tabPassword")}
                {tab === "password" && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Magic Link tab */}
          {tab === "magic-link" && (
            <form onSubmit={handleMagicLink} className="space-y-6">
              <p className="text-sm text-text-secondary">{t("magicLinkEnterEmail")}</p>
              <Input
                id="email-magic"
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
                {t("magicLinkSend")}
              </Button>
            </form>
          )}

          {/* Password tab */}
          {tab === "password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-6">
              <Input
                id="email-pw"
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
              <div className="text-right">
                <Link href="/forgot-password" className="text-sm text-primary-600 hover:text-primary-700">
                  {t("forgotPassword")}
                </Link>
              </div>
              <Button
                type="submit"
                variant="primary"
                isLoading={loading}
                icon={<ArrowRight />}
                className="w-full"
              >
                {t("emailSignIn")}
              </Button>
            </form>
          )}

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-surface px-2 text-text-tertiary">{t("orContinueWith")}</span>
            </div>
          </div>

          {/* Google button */}
          <button
            onClick={handleGoogle}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-white px-4 py-2.5 text-sm font-medium text-text-primary shadow-sm hover:bg-surface-alt transition-colors"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            {t("googleSignIn")}
          </button>

          <p className="text-center text-sm text-text-secondary">
            {t("noAccount")}{" "}
            <Link href="/signup" className="font-medium text-primary-600 hover:text-primary-700">
              {t("signup")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
