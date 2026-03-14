"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { LayoutDashboard, MessageCircle, Scale, Settings } from "./icons";

interface MobileNavProps {
  activePage: "dashboard" | "chat" | "attorneys" | "settings" | "pricing";
}

export function MobileNav({ activePage }: MobileNavProps) {
  const t = useTranslations("nav");

  const navItems = [
    { key: "dashboard", href: "/dashboard", icon: LayoutDashboard },
    { key: "chat", href: "/chat", icon: MessageCircle },
    { key: "attorneys", href: "/attorneys", icon: Scale },
    { key: "settings", href: "/settings", icon: Settings },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-surface md:hidden">
      <div className="flex justify-around py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.key;
          return (
            <Link
              key={item.key}
              href={item.href}
              className={`flex flex-col items-center px-3 py-2 text-xs font-medium min-w-[64px] transition-colors relative ${
                isActive ? "text-primary-600" : "text-text-secondary"
              }`}
            >
              {isActive && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary-600 rounded-full" />
              )}
              <Icon className="h-5 w-5 mb-1" />
              {t(item.key)}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
