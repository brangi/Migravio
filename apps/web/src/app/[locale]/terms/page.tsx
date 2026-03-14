"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import LanguageSwitcher from "@/components/language-switcher";
import { Logo } from "@/components/logo";
import { useAuth } from "@/lib/auth-context";
import { AppHeader } from "@/components/app-header";
import { AppFooter } from "@/components/footer";

export default function TermsPage() {
  const t = useTranslations();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-surface">
      {/* Header: auth-aware */}
      {user ? (
        <AppHeader />
      ) : (
        <header className="border-b border-border bg-surface">
          <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4">
            <Link href="/" className="transition-opacity hover:opacity-80">
              <Logo size="sm" variant="full" />
            </Link>
            <LanguageSwitcher />
          </div>
        </header>
      )}

      {/* Main Content */}
      <main className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8">
          <Link
            href={user ? "/dashboard" : "/"}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            ← {t("legal.backToHome")}
          </Link>
        </div>

        <article className="prose prose-gray max-w-none">
          <h1 className="mb-2 text-4xl font-[var(--font-display)] font-bold text-text-primary">
            {t("legal.termsTitle")}
          </h1>
          <p className="mb-12 text-sm text-text-tertiary">
            {t("legal.lastUpdated")}
          </p>

          {/* Acceptance of Terms */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              1. Acceptance of Terms
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              By accessing or using Migravio (the "Service"), you agree to be bound by these Terms of Service ("Terms").
              If you do not agree to these Terms, please do not use the Service.
            </p>
            <p className="text-base leading-relaxed text-text-secondary">
              These Terms constitute a legally binding agreement between you and Migravio. By creating an account or
              using any part of our Service, you confirm that you have read, understood, and agree to these Terms.
            </p>
          </section>

          {/* Service Description */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              2. Service Description
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              Migravio is an AI-powered immigration information platform designed to help immigrants in the United States
              navigate the immigration system. We provide educational content, informational tools, and connections to
              licensed immigration attorneys.
            </p>
            <div className="mb-4 rounded-r-lg border-l-4 border-warning bg-amber-50 p-4">
              <p className="font-semibold text-amber-900">Important Disclaimer</p>
              <p className="mt-2 text-base text-amber-800">
                <strong>Migravio is NOT a law firm.</strong> We do NOT provide legal advice, legal representation,
                or legal services. The information provided through our AI assistant and platform is for general
                informational and educational purposes only and should not be considered legal advice for your
                specific situation.
              </p>
            </div>
            <p className="text-base leading-relaxed text-text-secondary">
              Any information, answers, or guidance provided by our AI assistant are generated based on publicly
              available immigration information and should not be relied upon as a substitute for consultation with
              a qualified immigration attorney.
            </p>
          </section>

          {/* User Accounts */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              3. User Accounts
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              To access certain features of the Service, you must create an account. You agree to:
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-text-secondary">
              <li>Provide accurate, current, and complete information during registration</li>
              <li>Maintain and promptly update your account information</li>
              <li>Maintain the security of your password and account credentials</li>
              <li>Immediately notify us of any unauthorized use of your account</li>
              <li>Accept responsibility for all activities that occur under your account</li>
            </ul>
            <p className="text-base leading-relaxed text-text-secondary">
              You must be at least 18 years old to create an account. We reserve the right to suspend or terminate
              accounts that violate these Terms or are used for fraudulent or illegal purposes.
            </p>
          </section>

          {/* AI Disclaimers */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              4. AI Assistant Disclaimers
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              Our AI assistant is designed to provide general immigration information based on publicly available
              resources, including USCIS policy manuals, form instructions, and immigration law overviews.
            </p>
            <div className="mb-4 space-y-3">
              <div className="rounded-lg bg-surface-alt p-4">
                <p className="font-medium text-text-primary">No Legal Advice</p>
                <p className="mt-1 text-base text-text-secondary">
                  The AI assistant does not provide legal advice. Responses are for informational purposes only
                  and should not be construed as legal guidance for your specific case.
                </p>
              </div>
              <div className="rounded-lg bg-surface-alt p-4">
                <p className="font-medium text-text-primary">Potential Errors</p>
                <p className="mt-1 text-base text-text-secondary">
                  While we strive for accuracy, AI-generated responses may contain errors, omissions, or outdated
                  information. Always verify critical information with official USCIS sources or a licensed attorney.
                </p>
              </div>
              <div className="rounded-lg bg-surface-alt p-4">
                <p className="font-medium text-text-primary">No Guaranteed Outcomes</p>
                <p className="mt-1 text-base text-text-secondary">
                  Using our Service does not guarantee any particular outcome in your immigration case. Immigration
                  decisions are made solely by USCIS and other government agencies.
                </p>
              </div>
            </div>
            <p className="text-base leading-relaxed text-text-secondary">
              For complex legal matters, court proceedings, removal defense, asylum cases, appeals, or any situation
              involving an RFE (Request for Evidence), NOID (Notice of Intent to Deny), or denial, we strongly
              recommend consulting with a licensed immigration attorney.
            </p>
          </section>

          {/* Attorney Referrals */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              5. Attorney Referrals
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              Migravio facilitates introductions between users and licensed immigration attorneys. When you request
              an introduction to an attorney through our platform:
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-text-secondary">
              <li>
                Migravio acts solely as an intermediary to connect you with attorneys in our network
              </li>
              <li>
                We do not guarantee that any attorney will accept your case or provide specific outcomes
              </li>
              <li>
                Any attorney-client relationship formed is solely between you and the attorney
              </li>
              <li>
                Migravio is not responsible for the quality, timeliness, or outcome of legal services provided
              </li>
              <li>
                Fees, engagement terms, and scope of representation are between you and the attorney
              </li>
            </ul>
            <p className="text-base leading-relaxed text-text-secondary">
              While we vet attorneys in our network for proper licensing and good standing, we make no guarantees
              about their performance or suitability for your specific case.
            </p>
          </section>

          {/* Subscription & Payments */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              6. Subscription & Payments
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              Migravio offers free and paid subscription plans. By subscribing to a paid plan, you agree to:
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-text-secondary">
              <li>
                Pay all fees associated with your chosen subscription plan
              </li>
              <li>
                Provide accurate and current payment information
              </li>
              <li>
                Authorize recurring charges for monthly or annual subscriptions until canceled
              </li>
            </ul>
            <div className="mb-4 rounded-lg border border-border bg-surface-alt p-4">
              <p className="mb-2 font-medium text-text-primary">Billing & Cancellation</p>
              <ul className="list-inside list-disc space-y-2 text-base text-text-secondary">
                <li>Monthly subscriptions renew automatically each month</li>
                <li>Annual subscriptions renew automatically each year</li>
                <li>You may cancel your subscription at any time through your account settings</li>
                <li>Cancellations take effect at the end of your current billing period</li>
                <li>No refunds are provided for partial months or unused portions of paid subscriptions</li>
                <li>Annual plans may be eligible for pro-rated refunds within the first 30 days</li>
              </ul>
            </div>
            <p className="text-base leading-relaxed text-text-secondary">
              We reserve the right to modify pricing with 30 days' notice to active subscribers. Price changes
              do not affect your current billing cycle but will apply upon renewal.
            </p>
          </section>

          {/* User Data & Privacy */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              7. User Data & Privacy
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              Your privacy is important to us. Our collection, use, and protection of your personal information
              is governed by our{" "}
              <Link href="/privacy" className="text-primary-600 hover:text-primary-700 underline">
                Privacy Policy
              </Link>
              , which is incorporated into these Terms by reference.
            </p>
            <div className="mb-4 rounded-r-lg border-l-4 border-primary-300 bg-primary-50 p-4">
              <p className="font-semibold text-primary-900">Our Privacy Commitment</p>
              <p className="mt-2 text-base text-primary-800">
                We do NOT sell your data. We do NOT share your immigration information with third parties except
                as necessary to provide the Service (e.g., AI processing, payment processing) or when YOU
                explicitly request an attorney introduction.
              </p>
            </div>
            <p className="text-base leading-relaxed text-text-secondary">
              You retain ownership of all content you submit to the Service, including chat messages and profile
              information. By using the Service, you grant us a limited license to use this content solely to
              provide and improve the Service.
            </p>
          </section>

          {/* Limitation of Liability */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              8. Limitation of Liability
            </h2>
            <p className="mb-4 text-base font-medium uppercase tracking-wide text-text-primary">
              IMPORTANT LEGAL DISCLAIMER
            </p>
            <div className="mb-4 rounded-lg border-2 border-border-strong bg-surface-alt p-6">
              <p className="mb-4 text-base leading-relaxed text-text-secondary">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, MIGRAVIO AND ITS AFFILIATES, OFFICERS, EMPLOYEES, AND
                PARTNERS SHALL NOT BE LIABLE FOR:
              </p>
              <ul className="mb-4 list-inside list-disc space-y-2 text-base text-text-secondary">
                <li>
                  Any immigration outcomes, case decisions, denials, or delays resulting from information
                  obtained through the Service
                </li>
                <li>
                  Errors, omissions, or inaccuracies in AI-generated responses or platform content
                </li>
                <li>
                  Actions taken by users based on information provided through the Service
                </li>
                <li>
                  The quality, outcome, or conduct of attorneys in our referral network
                </li>
                <li>
                  Any indirect, incidental, special, consequential, or punitive damages
                </li>
                <li>
                  Loss of profits, data, use, goodwill, or other intangible losses
                </li>
              </ul>
            </div>
            <p className="text-base leading-relaxed text-text-secondary">
              Our total liability to you for any claims arising from your use of the Service shall not exceed
              the amount you paid to Migravio in the twelve (12) months preceding the claim.
            </p>
          </section>

          {/* Modifications to Terms */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              9. Modifications to Terms
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              We reserve the right to modify these Terms at any time. When we make material changes, we will:
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-text-secondary">
              <li>Update the "Last updated" date at the top of this page</li>
              <li>Notify you via email if you have an active account</li>
              <li>Provide prominent notice on our platform for significant changes</li>
            </ul>
            <p className="text-base leading-relaxed text-text-secondary">
              Your continued use of the Service after changes take effect constitutes acceptance of the modified
              Terms. If you do not agree to the changes, you must stop using the Service and cancel your account.
            </p>
          </section>

          {/* Governing Law */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              10. Governing Law
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              These Terms shall be governed by and construed in accordance with the laws of the State of California,
              United States, without regard to its conflict of law provisions.
            </p>
            <p className="text-base leading-relaxed text-text-secondary">
              Any disputes arising from these Terms or your use of the Service shall be resolved in the state or
              federal courts located in California, and you consent to the exclusive jurisdiction of such courts.
            </p>
          </section>

          {/* Contact */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              11. Contact Information
            </h2>
            <p className="mb-4 text-base leading-relaxed text-text-secondary">
              If you have questions about these Terms of Service, please contact us at:
            </p>
            <div className="rounded-lg border border-border bg-surface-alt p-4">
              <p className="text-base text-text-primary">
                <strong>Email:</strong>{" "}
                <a href="mailto:support@migravio.ai" className="text-primary-600 hover:text-primary-700">
                  support@migravio.ai
                </a>
              </p>
            </div>
          </section>

          {/* Entire Agreement */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
              12. Entire Agreement
            </h2>
            <p className="text-base leading-relaxed text-text-secondary">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and
              Migravio regarding your use of the Service and supersede all prior agreements and understandings.
            </p>
          </section>

          {/* Final Disclaimer */}
          <div className="mt-12 rounded-lg border-2 border-primary-300 bg-primary-50 p-6">
            <p className="mb-2 text-lg font-[var(--font-display)] font-semibold text-primary-900">
              Remember
            </p>
            <p className="text-base leading-relaxed text-primary-800">
              Migravio provides legal information, not legal advice. We are not a law firm. For complex
              immigration matters, always consult with a licensed immigration attorney who can evaluate
              your specific situation and provide personalized legal guidance.
            </p>
          </div>
        </article>

        {/* Back to Home Link */}
        <div className="mt-12 border-t border-border pt-8">
          <Link
            href={user ? "/dashboard" : "/"}
            className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            ← {t("legal.backToHome")}
          </Link>
        </div>
      </main>

      {/* Footer: auth-aware */}
      {user ? (
        <AppFooter />
      ) : (
        <footer className="border-t border-border bg-surface-alt py-8">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <p className="mb-4 text-sm text-text-secondary">
              {t("footer.disclaimer")}
            </p>
            <div className="flex justify-center gap-6 text-sm">
              <Link
                href="/terms"
                className="text-text-secondary hover:text-text-primary"
              >
                {t("footer.terms")}
              </Link>
              <Link
                href="/privacy"
                className="text-text-secondary hover:text-text-primary"
              >
                {t("footer.privacy")}
              </Link>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}
