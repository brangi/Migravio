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
  GoogleAuthProvider,
  type User,
} from "firebase/auth";
import { doc, getDoc, setDoc, serverTimestamp } from "firebase/firestore";
import { auth, db } from "./firebase";

interface UserProfile {
  language: string;
  visaType: string;
  visaExpiry: Date | null;
  priorityDate: Date | null;
  onboardingComplete: boolean;
  subscription: {
    plan: "free" | "pro" | "premium";
    status: string;
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
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

const googleProvider = new GoogleAuthProvider();

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
    const credential = await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );
    await setDoc(doc(db, "users", credential.user.uid), {
      email: credential.user.email,
      displayName: credential.user.displayName || "",
      language: "en",
      visaType: "",
      onboardingComplete: false,
      subscription: { plan: "free", status: "active" },
      messageCount: 0,
      messageResetDate: serverTimestamp(),
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
  };

  const signInWithGoogle = async () => {
    const credential = await signInWithPopup(auth, googleProvider);
    const docRef = doc(db, "users", credential.user.uid);
    const docSnap = await getDoc(docRef);
    if (!docSnap.exists()) {
      await setDoc(docRef, {
        email: credential.user.email,
        displayName: credential.user.displayName || "",
        photoURL: credential.user.photoURL || "",
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
