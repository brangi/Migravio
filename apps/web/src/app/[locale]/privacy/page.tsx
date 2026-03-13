"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import LanguageSwitcher from "@/components/language-switcher";

export default function PrivacyPage() {
  const t = useTranslations();

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4">
          <Link href="/" className="text-xl font-bold text-blue-700">
            {t("common.appName")}
          </Link>
          <LanguageSwitcher />
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8">
          <Link
            href="/"
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            ← {t("legal.backToHome")}
          </Link>
        </div>

        <article className="prose prose-gray max-w-none">
          <h1 className="mb-2 text-4xl font-bold text-gray-900">
            {t("legal.privacyTitle")}
          </h1>
          <p className="mb-12 text-sm text-gray-500">
            {t("legal.lastUpdated")}
          </p>

          {/* Introduction */}
          <section className="mb-10">
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              At Migravio, we understand that your immigration information is deeply personal and sensitive.
              This Privacy Policy explains how we collect, use, protect, and share your information when you
              use our Service.
            </p>
            <div className="mb-4 rounded-lg border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="font-semibold text-blue-900">Our Core Privacy Promise</p>
              <p className="mt-2 text-base text-blue-800">
                <strong>We do NOT sell your data.</strong> We do NOT share your immigration information with
                third parties except as described in this policy or when YOU explicitly request it.
              </p>
            </div>
            <p className="text-base leading-relaxed text-gray-700">
              By using Migravio, you agree to the collection and use of information in accordance with this
              Privacy Policy.
            </p>
          </section>

          {/* Information We Collect */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              1. Information We Collect
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We collect several types of information to provide and improve our Service.
            </p>

            <div className="mb-6">
              <h3 className="mb-3 text-xl font-semibold text-gray-900">
                Account Information
              </h3>
              <p className="mb-3 text-base text-gray-700">
                When you create an account, we collect:
              </p>
              <ul className="list-inside list-disc space-y-2 text-base text-gray-700">
                <li>Email address</li>
                <li>Name (if provided)</li>
                <li>Password (encrypted and never stored in plain text)</li>
                <li>Profile preferences (language selection, notification settings)</li>
              </ul>
            </div>

            <div className="mb-6">
              <h3 className="mb-3 text-xl font-semibold text-gray-900">
                Immigration Data
              </h3>
              <p className="mb-3 text-base text-gray-700">
                To personalize your experience and provide relevant information, we collect:
              </p>
              <ul className="list-inside list-disc space-y-2 text-base text-gray-700">
                <li>Visa type and status</li>
                <li>Important dates (visa expiration, priority date)</li>
                <li>Country of origin (optional)</li>
                <li>Immigration goals and concerns</li>
              </ul>
              <p className="mt-3 text-base text-gray-700">
                This information is stored securely and used solely to personalize your dashboard and AI responses.
              </p>
            </div>

            <div className="mb-6">
              <h3 className="mb-3 text-xl font-semibold text-gray-900">
                Chat Messages and Conversations
              </h3>
              <p className="mb-3 text-base text-gray-700">
                When you interact with our AI assistant, we collect:
              </p>
              <ul className="list-inside list-disc space-y-2 text-base text-gray-700">
                <li>Your questions and messages</li>
                <li>AI-generated responses</li>
                <li>Conversation history and timestamps</li>
                <li>Feedback on AI responses (if provided)</li>
              </ul>
              <p className="mt-3 text-base text-gray-700">
                Chat messages are stored in your account for your benefit, allowing you to reference past
                conversations and track your immigration journey over time.
              </p>
            </div>

            <div className="mb-6">
              <h3 className="mb-3 text-xl font-semibold text-gray-900">
                Usage and Analytics Data
              </h3>
              <p className="mb-3 text-base text-gray-700">
                To improve our Service, we automatically collect:
              </p>
              <ul className="list-inside list-disc space-y-2 text-base text-gray-700">
                <li>Device information (browser type, operating system)</li>
                <li>IP address and general location (city/state level)</li>
                <li>Pages visited and features used</li>
                <li>Time spent on different pages</li>
                <li>Error logs and performance metrics</li>
              </ul>
            </div>

            <div className="mb-6">
              <h3 className="mb-3 text-xl font-semibold text-gray-900">
                Payment Information
              </h3>
              <p className="text-base text-gray-700">
                When you subscribe to a paid plan, we collect payment information through our payment processor,
                Stripe. We do NOT store your full credit card details on our servers. Stripe provides us with
                limited information (last 4 digits, expiration date, card brand) for billing purposes.
              </p>
            </div>
          </section>

          {/* How We Use Your Information */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              2. How We Use Your Information
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We use the information we collect for the following purposes:
            </p>

            <div className="mb-4 space-y-3">
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Provide Immigration Information</p>
                <p className="mt-1 text-base text-gray-700">
                  To answer your questions, personalize AI responses based on your visa type, and provide
                  relevant immigration guidance.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Personalize Your Dashboard</p>
                <p className="mt-1 text-base text-gray-700">
                  To show you visa status, countdown timers, relevant policy alerts, and action items
                  tailored to your specific immigration situation.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Improve Our AI</p>
                <p className="mt-1 text-base text-gray-700">
                  To analyze conversation patterns, identify common questions, improve AI accuracy, and
                  detect when users need attorney referrals.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Communication</p>
                <p className="mt-1 text-base text-gray-700">
                  To send you important account notifications, visa deadline reminders, policy alerts
                  affecting your visa type, and service updates.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Process Payments</p>
                <p className="mt-1 text-base text-gray-700">
                  To manage subscriptions, process billing, and handle refunds or cancellations.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Security and Fraud Prevention</p>
                <p className="mt-1 text-base text-gray-700">
                  To detect and prevent unauthorized access, abuse, and fraudulent activity on our platform.
                </p>
              </div>
            </div>
          </section>

          {/* AI Processing */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              3. AI Processing and Third-Party Models
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              Our AI assistant uses advanced language models provided by third-party AI services (currently
              Claude by Anthropic, accessed via OpenRouter) to generate responses to your questions.
            </p>
            <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <p className="mb-2 font-medium text-gray-900">How AI Processing Works</p>
              <ul className="list-inside list-disc space-y-2 text-base text-gray-700">
                <li>
                  When you send a message, it is transmitted to the AI service provider for processing
                </li>
                <li>
                  The AI service processes your message to generate a response
                </li>
                <li>
                  Your messages are used ONLY to generate responses for your conversation
                </li>
                <li>
                  We do NOT allow AI providers to use your data to train their models
                </li>
                <li>
                  Messages are processed in real-time and not permanently stored by AI providers
                </li>
              </ul>
            </div>
            <p className="text-base leading-relaxed text-gray-700">
              While we work with trusted AI providers who maintain strong privacy and security practices,
              please be aware that your messages are transmitted to these third-party services for processing.
            </p>
          </section>

          {/* Data Sharing */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              4. How We Share Your Information
            </h2>
            <div className="mb-4 rounded-lg border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="font-semibold text-blue-900">We Do NOT Sell Your Data</p>
              <p className="mt-2 text-base text-blue-800">
                We will never sell, rent, or trade your personal information or immigration data to third
                parties for marketing purposes.
              </p>
            </div>

            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We share your information only in the following limited circumstances:
            </p>

            <div className="mb-4 space-y-3">
              <div className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">With AI Service Providers</p>
                <p className="mt-1 text-base text-gray-700">
                  Your messages are sent to AI providers (OpenRouter, Anthropic) to generate responses.
                  These providers do NOT use your data for training or other purposes beyond providing
                  the AI service.
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">With Payment Processors</p>
                <p className="mt-1 text-base text-gray-700">
                  Payment information is processed by Stripe to handle subscriptions and billing. Stripe's
                  use of your information is governed by their privacy policy.
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">With Attorneys (Only When You Request)</p>
                <p className="mt-1 text-base text-gray-700">
                  When YOU explicitly request an introduction to an attorney, we share your name, contact
                  information, and a brief description of your situation with that attorney. This is done
                  ONLY at your request and with your explicit consent.
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">For Legal Compliance</p>
                <p className="mt-1 text-base text-gray-700">
                  We may disclose information if required by law, court order, or legal process, or to
                  protect the rights, property, or safety of Migravio, our users, or others.
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">In Business Transfers</p>
                <p className="mt-1 text-base text-gray-700">
                  If Migravio is involved in a merger, acquisition, or sale of assets, your information
                  may be transferred. We will notify you before your information is transferred and
                  becomes subject to a different privacy policy.
                </p>
              </div>
            </div>
          </section>

          {/* Data Storage & Security */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              5. Data Storage and Security
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We take the security of your information seriously and implement industry-standard measures
              to protect it.
            </p>

            <div className="mb-4 space-y-3">
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Where Your Data Is Stored</p>
                <p className="mt-1 text-base text-gray-700">
                  Your data is stored using Firebase (Google Cloud Platform), a secure, enterprise-grade
                  cloud infrastructure. All data is stored on servers located in the United States.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Encryption</p>
                <p className="mt-1 text-base text-gray-700">
                  All data transmitted between your device and our servers is encrypted using HTTPS/TLS.
                  Sensitive data is encrypted at rest in our database.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Access Controls</p>
                <p className="mt-1 text-base text-gray-700">
                  Access to user data is strictly limited to authorized personnel who need it to provide
                  and improve the Service. All access is logged and monitored.
                </p>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <p className="font-medium text-gray-900">Regular Security Audits</p>
                <p className="mt-1 text-base text-gray-700">
                  We regularly review our security practices and update them to address new threats and
                  vulnerabilities.
                </p>
              </div>
            </div>

            <p className="text-base leading-relaxed text-gray-700">
              While we implement strong security measures, no method of transmission or storage is 100%
              secure. We cannot guarantee absolute security of your information.
            </p>
          </section>

          {/* Your Rights */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              6. Your Rights and Choices
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              You have the following rights regarding your personal information:
            </p>

            <div className="mb-4 space-y-3">
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Access Your Data</p>
                <p className="mt-1 text-base text-blue-800">
                  You can view and download your account information, profile data, and chat history
                  through your account settings at any time.
                </p>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Correct Your Data</p>
                <p className="mt-1 text-base text-blue-800">
                  You can update your account information, visa details, and preferences directly in your
                  account settings.
                </p>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Delete Your Data</p>
                <p className="mt-1 text-base text-blue-800">
                  You can request deletion of your account and all associated data by contacting us at
                  privacy@migravio.ai. We will process your request within 30 days.
                </p>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Export Your Data</p>
                <p className="mt-1 text-base text-blue-800">
                  You can request a copy of your data in a portable format (JSON/CSV) by contacting us.
                </p>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Withdraw Consent</p>
                <p className="mt-1 text-base text-blue-800">
                  You can withdraw consent for optional data processing (e.g., marketing emails, analytics)
                  at any time through your account settings.
                </p>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="font-medium text-blue-900">Opt Out of Communications</p>
                <p className="mt-1 text-base text-blue-800">
                  You can unsubscribe from marketing emails by clicking the unsubscribe link in any email.
                  Note that we will still send you important account-related notifications.
                </p>
              </div>
            </div>
          </section>

          {/* Data Retention */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              7. Data Retention
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We retain your information for as long as necessary to provide the Service and fulfill the
              purposes described in this Privacy Policy.
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-gray-700">
              <li>
                <strong>Account data:</strong> Retained while your account is active
              </li>
              <li>
                <strong>Chat history:</strong> Retained in your account for your benefit unless you delete it
              </li>
              <li>
                <strong>Usage data:</strong> Aggregated and anonymized data may be retained indefinitely
                for analytics
              </li>
              <li>
                <strong>Billing data:</strong> Retained for up to 7 years for tax and accounting purposes
              </li>
            </ul>
            <p className="text-base leading-relaxed text-gray-700">
              When you delete your account, we delete your personal information within 30 days, except for
              data we are required to retain for legal or regulatory reasons.
            </p>
          </section>

          {/* Children's Privacy */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              8. Children's Privacy
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              Migravio is not intended for use by individuals under the age of 13. We do not knowingly
              collect personal information from children under 13.
            </p>
            <p className="text-base leading-relaxed text-gray-700">
              If you are a parent or guardian and believe your child has provided us with personal information,
              please contact us immediately at privacy@migravio.ai, and we will delete the information.
            </p>
          </section>

          {/* International Users */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              9. International Users
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              Migravio is based in the United States and designed for users in the United States. If you
              access our Service from outside the United States, your information will be transferred to,
              stored, and processed in the United States.
            </p>
            <p className="text-base leading-relaxed text-gray-700">
              By using our Service, you consent to the transfer of your information to the United States
              and agree that U.S. law governs the collection and use of your information.
            </p>
          </section>

          {/* Changes to Privacy Policy */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              10. Changes to This Privacy Policy
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              We may update this Privacy Policy from time to time to reflect changes in our practices or
              for legal, operational, or regulatory reasons.
            </p>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              When we make material changes, we will:
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-gray-700">
              <li>Update the "Last updated" date at the top of this page</li>
              <li>Notify you via email if you have an active account</li>
              <li>Provide prominent notice on our platform for significant changes</li>
            </ul>
            <p className="text-base leading-relaxed text-gray-700">
              Your continued use of the Service after changes take effect constitutes acceptance of the
              updated Privacy Policy.
            </p>
          </section>

          {/* Contact Information */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              11. Contact Us
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              If you have questions, concerns, or requests regarding this Privacy Policy or our data
              practices, please contact us:
            </p>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <p className="mb-2 text-base text-gray-900">
                <strong>Email:</strong>{" "}
                <a href="mailto:privacy@migravio.ai" className="text-blue-600 hover:text-blue-800">
                  privacy@migravio.ai
                </a>
              </p>
              <p className="text-base text-gray-900">
                <strong>For general support:</strong>{" "}
                <a href="mailto:support@migravio.ai" className="text-blue-600 hover:text-blue-800">
                  support@migravio.ai
                </a>
              </p>
            </div>
          </section>

          {/* California Privacy Rights */}
          <section className="mb-10">
            <h2 className="mb-4 text-2xl font-semibold text-gray-900">
              12. California Privacy Rights (CCPA)
            </h2>
            <p className="mb-4 text-base leading-relaxed text-gray-700">
              If you are a California resident, you have additional rights under the California Consumer
              Privacy Act (CCPA):
            </p>
            <ul className="mb-4 list-inside list-disc space-y-2 text-base text-gray-700">
              <li>
                Right to know what personal information we collect, use, and share
              </li>
              <li>
                Right to request deletion of your personal information
              </li>
              <li>
                Right to opt out of the "sale" of personal information (we do not sell data)
              </li>
              <li>
                Right to non-discrimination for exercising your CCPA rights
              </li>
            </ul>
            <p className="text-base leading-relaxed text-gray-700">
              To exercise these rights, contact us at privacy@migravio.ai with "CCPA Request" in the
              subject line.
            </p>
          </section>

          {/* Final Statement */}
          <div className="mt-12 rounded-lg border-2 border-blue-200 bg-blue-50 p-6">
            <p className="mb-2 text-lg font-semibold text-blue-900">
              Your Privacy Matters
            </p>
            <p className="text-base leading-relaxed text-blue-800">
              We are committed to protecting your privacy and handling your immigration data with the
              utmost care and security. We will never sell your data, and we only share it in the limited
              circumstances described in this policy. If you have any concerns, please don't hesitate to
              reach out to us.
            </p>
          </div>
        </article>

        {/* Back to Home Link */}
        <div className="mt-12 border-t border-gray-200 pt-8">
          <Link
            href="/"
            className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            ← {t("legal.backToHome")}
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50 py-8">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <p className="mb-4 text-sm text-gray-600">
            {t("footer.disclaimer")}
          </p>
          <div className="flex justify-center gap-6 text-sm">
            <Link
              href="/terms"
              className="text-gray-600 hover:text-gray-900"
            >
              {t("footer.terms")}
            </Link>
            <Link
              href="/privacy"
              className="text-gray-600 hover:text-gray-900"
            >
              {t("footer.privacy")}
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
