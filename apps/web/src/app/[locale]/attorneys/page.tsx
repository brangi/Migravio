"use client";

import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import { collection, addDoc, serverTimestamp, query, where, getDocs } from "firebase/firestore";
import { db } from "@/lib/firebase";

// Attorney data
const ATTORNEYS = [
  {
    id: "attorney-1",
    name: "Maria Rodriguez",
    specialties: ["Family-based immigration", "Removal defense"],
    languages: ["Spanish", "English"],
    states: ["CA", "TX"],
    bio: "Maria has over 15 years of experience helping families navigate the complex immigration system. She is passionate about keeping families together.",
  },
  {
    id: "attorney-2",
    name: "David Chen",
    specialties: ["Employment visas", "Business immigration"],
    languages: ["Mandarin", "English"],
    states: ["NY", "CA"],
    bio: "David specializes in H-1B, L-1, and O-1 visas for professionals and businesses. He has helped hundreds of companies sponsor employees successfully.",
  },
  {
    id: "attorney-3",
    name: "Sarah Williams",
    specialties: ["Asylum", "Refugee status", "Humanitarian visas"],
    languages: ["English", "French"],
    states: ["DC", "VA", "MD"],
    bio: "Sarah is dedicated to protecting those fleeing persecution. She works closely with nonprofit organizations and human rights advocates.",
  },
  {
    id: "attorney-4",
    name: "Raj Patel",
    specialties: ["Student visas", "OPT/CPT", "H-1B transfers"],
    languages: ["Hindi", "Gujarati", "English"],
    states: ["TX", "NJ"],
    bio: "Raj understands the unique challenges international students face. He helps students transition from F-1 to work visas seamlessly.",
  },
  {
    id: "attorney-5",
    name: "Ana Gutierrez",
    specialties: ["Naturalization", "Green cards", "DACA"],
    languages: ["Spanish", "English"],
    states: ["FL", "IL"],
    bio: "Ana is committed to helping immigrants achieve their dream of becoming U.S. citizens. She provides compassionate, expert guidance through every step.",
  },
];

const ALL_SPECIALTIES = Array.from(
  new Set(ATTORNEYS.flatMap((a) => a.specialties))
).sort();

function AttorneyCard({
  attorney,
  onRequestIntro,
  isRequested,
}: {
  attorney: typeof ATTORNEYS[0];
  onRequestIntro: (attorney: typeof ATTORNEYS[0]) => void;
  isRequested: boolean;
}) {
  const t = useTranslations("attorneys");

  const specialtyColors = [
    "bg-blue-100 text-blue-700",
    "bg-green-100 text-green-700",
    "bg-purple-100 text-purple-700",
    "bg-orange-100 text-orange-700",
  ];

  return (
    <div className="flex flex-col rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      {/* Name */}
      <h3 className="text-xl font-bold text-gray-900">{attorney.name}</h3>

      {/* Specialties */}
      <div className="mt-3 flex flex-wrap gap-2">
        {attorney.specialties.map((specialty, idx) => (
          <span
            key={specialty}
            className={`rounded-full px-3 py-1 text-xs font-medium ${specialtyColors[idx % specialtyColors.length]}`}
          >
            {specialty}
          </span>
        ))}
      </div>

      {/* Bio */}
      <p className="mt-4 flex-1 text-sm text-gray-600">{attorney.bio}</p>

      {/* Languages */}
      <div className="mt-4 text-sm">
        <span className="font-medium text-gray-700">{t("languages")}:</span>{" "}
        <span className="text-gray-600">{attorney.languages.join(", ")}</span>
      </div>

      {/* States */}
      <div className="mt-2 text-sm">
        <span className="font-medium text-gray-700">{t("states")}:</span>{" "}
        <span className="text-gray-600">{attorney.states.join(", ")}</span>
      </div>

      {/* CTA Button */}
      <button
        onClick={() => onRequestIntro(attorney)}
        disabled={isRequested}
        className={`mt-6 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors ${
          isRequested
            ? "cursor-not-allowed bg-green-100 text-green-700"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {isRequested ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            {t("introSent")}
          </span>
        ) : (
          t("requestIntro")
        )}
      </button>
    </div>
  );
}

function ConfirmationModal({
  attorney,
  onConfirm,
  onCancel,
}: {
  attorney: typeof ATTORNEYS[0] | null;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations("attorneys");

  if (!attorney) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-bold text-gray-900">
          Request introduction to {attorney.name}?
        </h3>
        <p className="mt-3 text-sm text-gray-600">{t("introDescription")}</p>

        <div className="mt-6 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AttorneysPage() {
  const t = useTranslations("attorneys");
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const { user, profile, loading, signOut } = useAuth();
  const router = useRouter();

  const [selectedSpecialty, setSelectedSpecialty] = useState<string | null>(null);
  const [confirmAttorney, setConfirmAttorney] = useState<typeof ATTORNEYS[0] | null>(null);
  const [requestedAttorneys, setRequestedAttorneys] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  // Fetch existing referrals
  useEffect(() => {
    async function fetchReferrals() {
      if (!user) return;

      const q = query(
        collection(db, "referrals"),
        where("userId", "==", user.uid)
      );
      const snapshot = await getDocs(q);
      const requested = new Set<string>();
      snapshot.forEach((doc) => {
        requested.add(doc.data().attorneyId);
      });
      setRequestedAttorneys(requested);
    }

    if (user) {
      fetchReferrals();
    }
  }, [user]);

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const filteredAttorneys = selectedSpecialty
    ? ATTORNEYS.filter((a) => a.specialties.includes(selectedSpecialty))
    : ATTORNEYS;

  const handleRequestIntro = (attorney: typeof ATTORNEYS[0]) => {
    setConfirmAttorney(attorney);
  };

  const handleConfirm = async () => {
    if (!confirmAttorney || !user || submitting) return;

    setSubmitting(true);
    try {
      await addDoc(collection(db, "referrals"), {
        userId: user.uid,
        userEmail: user.email,
        attorneyId: confirmAttorney.id,
        attorneyName: confirmAttorney.name,
        status: "requested",
        visaType: profile.visaType || "",
        createdAt: serverTimestamp(),
      });

      setRequestedAttorneys((prev) => new Set(prev).add(confirmAttorney.id));
      setConfirmAttorney(null);
    } catch (error) {
      console.error("Error creating referral:", error);
      alert("Failed to send introduction request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <span className="text-xl font-bold text-blue-700">Migravio</span>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("dashboard")}
            </Link>
            <Link
              href="/chat"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("chat")}
            </Link>
            <Link
              href="/attorneys"
              className="text-sm font-medium text-blue-600"
            >
              {tNav("attorneys")}
            </Link>
          </nav>
          <button
            onClick={signOut}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {tNav("signOut")}
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 pb-24 md:pb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t("title")}</h1>
        <p className="mt-2 text-gray-600">{t("subtitle")}</p>

        {/* Filter pills */}
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedSpecialty(null)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              selectedSpecialty === null
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
            }`}
          >
            All specialties
          </button>
          {ALL_SPECIALTIES.map((specialty) => (
            <button
              key={specialty}
              onClick={() => setSelectedSpecialty(specialty)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                selectedSpecialty === specialty
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
              }`}
            >
              {specialty}
            </button>
          ))}
        </div>

        {/* Attorney grid */}
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAttorneys.map((attorney) => (
            <AttorneyCard
              key={attorney.id}
              attorney={attorney}
              onRequestIntro={handleRequestIntro}
              isRequested={requestedAttorneys.has(attorney.id)}
            />
          ))}
        </div>

        {filteredAttorneys.length === 0 && (
          <div className="mt-8 rounded-lg border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">
              No attorneys found for this specialty. Try a different filter.
            </p>
          </div>
        )}
      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white md:hidden">
        <div className="flex justify-around py-2">
          <Link
            href="/dashboard"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            {tNav("dashboard")}
          </Link>
          <Link
            href="/chat"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            {tNav("chat")}
          </Link>
          <Link
            href="/attorneys"
            className="flex flex-col items-center p-2 text-xs font-medium text-blue-600"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {tNav("attorneys")}
          </Link>
        </div>
      </nav>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50 py-6 text-center text-sm text-gray-500">
        {tFooter("disclaimer")}
      </footer>

      {/* Confirmation Modal */}
      {confirmAttorney && (
        <ConfirmationModal
          attorney={confirmAttorney}
          onConfirm={handleConfirm}
          onCancel={() => setConfirmAttorney(null)}
        />
      )}
    </div>
  );
}
