"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  type User,
  type ActionCodeSettings,
} from "firebase/auth";
import { doc, getDoc, setDoc, serverTimestamp } from "firebase/firestore";
import { auth, db } from "./firebase";

const MAGIC_LINK_EMAIL_KEY = "migravio_magic_link_email";

interface UserProfile {
  language: string;
  visaType: string;
  visaExpiry: Date | null;
  priorityDate: Date | null;
  onboardingComplete: boolean;
  subscription: {
    plan: "free" | "pro" | "premium";
    status: string;
    stripeCustomerId?: string;
    stripeSubscriptionId?: string;
  };
  messageCount: number;
}

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeMagicLinkSignIn: (url: string) => Promise<boolean>;
  resetPassword: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

const googleProvider = new GoogleAuthProvider();

function getActionCodeSettings(): ActionCodeSettings {
  const baseUrl =
    typeof window !== "undefined"
      ? window.location.origin
      : "http://localhost:3000";
  return {
    url: `${baseUrl}/en/email-signin`,
    handleCodeInApp: true,
  };
}

async function ensureUserProfile(uid: string, email: string | null, displayName: string | null, photoURL: string | null) {
  const docRef = doc(db, "users", uid);
  const docSnap = await getDoc(docRef);
  if (!docSnap.exists()) {
    await setDoc(docRef, {
      email: email || "",
      displayName: displayName || "",
      photoURL: photoURL || "",
      language: "en",
      visaType: "",
      onboardingComplete: false,
      subscription: { plan: "free", status: "active" },
      messageCount: 0,
      messageResetDate: serverTimestamp(),
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async (uid: string) => {
    const docRef = doc(db, "users", uid);
    const docSnap = await getDoc(docRef);
    if (docSnap.exists()) {
      const data = docSnap.data();
      setProfile({
        language: data.language || "en",
        visaType: data.visaType || "",
        visaExpiry: data.visaExpiry?.toDate() || null,
        priorityDate: data.priorityDate?.toDate() || null,
        onboardingComplete: data.onboardingComplete || false,
        subscription: data.subscription || { plan: "free", status: "active" },
        messageCount: data.messageCount || 0,
      });
    } else {
      setProfile(null);
    }
  };

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user.uid);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        await fetchProfile(firebaseUser.uid);
      } else {
        setProfile(null);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  const signUp = async (email: string, password: string) => {
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    try {
      await ensureUserProfile(credential.user.uid, credential.user.email, credential.user.displayName, null);
    } catch (err) {
      console.error("Failed to create user profile (will retry on next load):", err);
    }
  };

  const signInWithGoogle = async () => {
    const credential = await signInWithPopup(auth, googleProvider);
    // Profile creation is best-effort — don't block sign-in if Firestore write fails
    try {
      await ensureUserProfile(credential.user.uid, credential.user.email, credential.user.displayName, credential.user.photoURL);
    } catch (err) {
      console.error("Failed to create user profile (will retry on next load):", err);
    }
  };

  const sendMagicLink = async (email: string) => {
    await sendSignInLinkToEmail(auth, email, getActionCodeSettings());
    if (typeof window !== "undefined") {
      window.localStorage.setItem(MAGIC_LINK_EMAIL_KEY, email);
    }
  };

  const completeMagicLinkSignIn = async (url: string): Promise<boolean> => {
    if (!isSignInWithEmailLink(auth, url)) {
      return false;
    }
    let email =
      typeof window !== "undefined"
        ? window.localStorage.getItem(MAGIC_LINK_EMAIL_KEY)
        : null;
    if (!email) {
      email = window.prompt("Please enter your email to confirm sign-in:");
    }
    if (!email) return false;

    const credential = await signInWithEmailLink(auth, email, url);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(MAGIC_LINK_EMAIL_KEY);
    }
    await ensureUserProfile(credential.user.uid, credential.user.email, credential.user.displayName, null);
    return true;
  };

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email);
  };

  const signOut = async () => {
    await firebaseSignOut(auth);
    setProfile(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        signIn,
        signUp,
        signInWithGoogle,
        sendMagicLink,
        completeMagicLinkSignIn,
        resetPassword,
        signOut,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
