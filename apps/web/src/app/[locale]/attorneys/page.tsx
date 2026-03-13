"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function AttorneysPage() {
  const t = useTranslations("attorneys");

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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">{t("title")}</h1>
        <p className="mt-2 text-gray-600">{t("subtitle")}</p>
        <p className="mt-8 text-sm text-gray-400">
          Attorney profiles coming in Sub-Project 4
        </p>
      </main>
    </div>
  );
}
