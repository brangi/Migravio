"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function ChatPage() {
  const t = useTranslations("chat");
  const tNav = useTranslations("nav");

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/dashboard" className="text-xl font-bold text-blue-700">
            Migravio
          </Link>
          <h1 className="text-sm font-medium text-gray-600">{t("title")}</h1>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">{t("title")}</h2>
          <p className="mt-2 text-sm text-gray-500">{t("disclaimer")}</p>
          <p className="mt-8 text-sm text-gray-400">
            Chat interface coming in Sub-Project 3
          </p>
        </div>
      </main>

      <footer className="border-t border-gray-100 bg-gray-50 py-4 text-center text-xs text-gray-400">
        {t("disclaimer")}
      </footer>
    </div>
  );
}
