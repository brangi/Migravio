"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import { collection, addDoc, serverTimestamp, query, where, getDocs } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { AppFooter } from "@/components/footer";
import { Button } from "@/components/button";
import { Globe, MapPin, CheckCircle2, Loader2 } from "@/components/icons";

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

  return (
    <div className="flex flex-col rounded-xl border border-border bg-white p-6 shadow-warm-sm hover:shadow-warm-md transition-shadow">
      {/* Name */}
      <h3 className="text-xl font-bold font-display text-text-primary">{attorney.name}</h3>

      {/* Specialties */}
      <div className="mt-3 flex flex-wrap gap-2">
        {attorney.specialties.map((specialty) => (
          <span
            key={specialty}
            className="rounded-full px-3 py-1 text-xs font-medium bg-primary-50 text-primary-700"
          >
            {specialty}
          </span>
        ))}
      </div>

      {/* Bio */}
      <p className="mt-4 flex-1 text-sm text-text-secondary">{attorney.bio}</p>

      {/* Languages */}
      <div className="mt-4 text-sm flex items-center gap-2">
        <Globe className="h-4 w-4 text-text-tertiary flex-shrink-0" />
        <span className="font-medium text-text-secondary">{t("languages")}:</span>{" "}
        <span className="text-text-tertiary">{attorney.languages.join(", ")}</span>
      </div>

      {/* States */}
      <div className="mt-2 text-sm flex items-center gap-2">
        <MapPin className="h-4 w-4 text-text-tertiary flex-shrink-0" />
        <span className="font-medium text-text-secondary">{t("states")}:</span>{" "}
        <span className="text-text-tertiary">{attorney.states.join(", ")}</span>
      </div>

      {/* CTA Button */}
      <button
        onClick={() => onRequestIntro(attorney)}
        disabled={isRequested}
        className={`mt-6 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors ${
          isRequested
            ? "cursor-not-allowed bg-green-50 text-green-700 border border-green-200 flex items-center justify-center gap-2"
            : "bg-primary-600 text-white hover:bg-primary-700"
        }`}
      >
        {isRequested ? (
          <>
            <CheckCircle2 className="h-4 w-4" />
            {t("introSent")}
          </>
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-warm-xl">
        <h3 className="text-lg font-bold font-display text-text-primary">
          Request introduction to {attorney.name}?
        </h3>
        <p className="mt-3 text-sm text-text-secondary">{t("introDescription")}</p>

        <div className="mt-6 flex gap-3">
          <Button variant="secondary" onClick={onCancel} className="flex-1">
            Cancel
          </Button>
          <Button variant="primary" onClick={onConfirm} className="flex-1">
            Confirm
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function AttorneysPage() {
  const t = useTranslations("attorneys");
  const { user, profile, loading } = useAuth();
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
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
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
    <div className="flex min-h-screen flex-col bg-surface">
      <AppHeader activePage="attorneys" />

      {/* Main content */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 pb-16 md:pb-8">
        <h1 className="text-3xl font-bold font-display text-text-primary">{t("title")}</h1>
        <p className="mt-2 text-text-secondary">{t("subtitle")}</p>

        {/* Filter pills */}
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedSpecialty(null)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              selectedSpecialty === null
                ? "bg-primary-600 text-white"
                : "bg-white text-text-secondary hover:bg-surface-alt border border-border"
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
                  ? "bg-primary-600 text-white"
                  : "bg-white text-text-secondary hover:bg-surface-alt border border-border"
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
          <div className="mt-8 rounded-lg border border-border bg-white p-8 text-center">
            <p className="text-text-secondary">
              No attorneys found for this specialty. Try a different filter.
            </p>
          </div>
        )}
      </main>

      <MobileNav activePage="attorneys" />
      <AppFooter />

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
