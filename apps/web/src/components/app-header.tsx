"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useAuth } from "@/lib/auth-context";
import { Logo } from "./logo";
import LanguageSwitcher from "./language-switcher";
import { LayoutDashboard, MessageCircle, Scale, CreditCard, LogOut, ArrowRight } from "./icons";

interface AppHeaderProps {
  activePage?: "dashboard" | "chat" | "attorneys" | "pricing" | "settings";
}

export function AppHeader({ activePage }: AppHeaderProps) {
  const t = useTranslations("nav");
  const tAuth = useTranslations("auth");
  const { user, signOut } = useAuth();

  const authNavItems = [
    { key: "dashboard", href: "/dashboard", icon: LayoutDashboard },
    { key: "chat", href: "/chat", icon: MessageCircle },
    { key: "attorneys", href: "/attorneys", icon: Scale },
    { key: "pricing", href: "/pricing", icon: CreditCard },
  ];

  const publicNavItems = [
    { key: "pricing", href: "/pricing", icon: CreditCard },
  ];

  const navItems = user ? authNavItems : publicNavItems;

  return (
    <header className="sticky top-0 z-40 border-b border-border-strong bg-white shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-6">
        {/* Logo */}
        <Link href={user ? "/dashboard" : "/"} className="flex-shrink-0">
          <Logo size="md" variant="full" className="hidden sm:flex" />
          <Logo size="md" variant="icon" className="sm:hidden" />
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.key;
            return (
              <Link
                key={item.key}
                href={item.href}
                className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors relative ${
                  isActive
                    ? "text-primary-600"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-alt"
                }`}
              >
                <Icon className="h-4 w-4" />
                {t(item.key)}
                {isActive && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary-600 rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          {user ? (
            <button
              onClick={signOut}
              className="hidden md:flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              aria-label={t("signOut")}
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden lg:inline">{t("signOut")}</span>
            </button>
          ) : (
            <Link
              href="/login"
              className="hidden md:flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
            >
              {tAuth("login")}
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
