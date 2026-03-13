"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link } from "@/i18n/navigation";

export default function HomePage() {
  const t = useTranslations();
  const { user, loading } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-gray-100 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <span className="text-xl font-bold text-blue-700">
            {t("common.appName")}
          </span>
          <div className="flex items-center gap-3">
            {loading ? null : user ? (
              <Link
                href="/dashboard"
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {t("nav.dashboard")}
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  {t("auth.login")}
                </Link>
                <Link
                  href="/signup"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  {t("auth.signup")}
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          {t("common.tagline")}
        </h1>
        <p className="mt-6 max-w-lg text-lg text-gray-600">
          Navigate the U.S. immigration system with confidence. Get instant
          answers in your language, powered by AI.
        </p>
        <div className="mt-8 flex gap-4">
          <Link
            href={user ? "/dashboard" : "/signup"}
            className="rounded-lg bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-blue-700"
          >
            {t("common.getStarted")}
          </Link>
        </div>
      </main>

      <footer className="border-t border-gray-100 bg-gray-50 py-6 text-center text-sm text-gray-500">
        {t("footer.disclaimer")}
      </footer>
    </div>
  );
}
