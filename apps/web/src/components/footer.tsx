import { useTranslations } from "next-intl";
import { Logo } from "./logo";
import { Link } from "@/i18n/navigation";

export function AppFooter() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t border-border bg-surface-alt py-6 text-center">
      <p className="text-sm text-text-tertiary max-w-3xl mx-auto px-4">
        {t("disclaimer")}
      </p>
    </footer>
  );
}

export function LandingFooter() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t border-border bg-surface-alt">
      <div className="mx-auto max-w-7xl px-4 py-12 lg:px-6">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <Logo size="md" variant="full" />
            <p className="mt-4 text-sm text-text-tertiary">
              {t("tagline")}
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-3">
              {t("product")}
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/pricing" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("pricing")}
                </Link>
              </li>
              <li>
                <Link href="/attorneys" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("attorneys")}
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-3">
              {t("resources")}
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("about")}
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("privacy")}
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("terms")}
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-3">
              {t("support")}
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="mailto:support@migravio.ai" className="text-text-secondary hover:text-text-primary transition-colors">
                  {t("contact")}
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Disclaimer & Copyright */}
        <div className="mt-12 border-t border-border pt-8 space-y-4">
          <p className="text-sm text-text-tertiary text-center">
            {t("disclaimer")}
          </p>
          <p className="text-xs text-text-tertiary text-center">
            © {new Date().getFullYear()} Migravio. {t("copyright")}
          </p>
        </div>
      </div>
    </footer>
  );
}
