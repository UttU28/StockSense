import React, { createContext, useContext, useEffect, useReducer, useState } from "react";
import type { User } from "firebase/auth";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  updateProfile,
} from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

type AuthContextValue = {
  user: User | null;
  idToken: string | null;
  /** Get a fresh token (forces refresh if expired). Use before sensitive API calls. */
  getIdToken: () => Promise<string | null>;
  loading: boolean;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  updatePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  updateDisplayName: (displayName: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [, forceUpdate] = useReducer((x: number) => x + 1, 0);

  const auth = getFirebaseAuth();

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (u) => {
      setUser(u ?? null);
      if (u) {
        try {
          const token = await u.getIdToken();
          setIdToken(token);
        } catch {
          setIdToken(null);
        }
      } else {
        setIdToken(null);
      }
      setLoading(false);
    });
    return () => unsub();
  }, [auth]);

  const signUp = async (name: string, email: string, password: string) => {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    if (cred.user) {
      await updateProfile(cred.user, { displayName: name });
      const token = await cred.user.getIdToken();
      setIdToken(token);
      setUser(cred.user);
      // Register user in backend Firestore
      try {
        await fetch(`${API_BASE}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idToken: token, displayName: name, email }),
        });
      } catch (e) {
        console.warn("Backend register failed:", e);
      }
    }
  };

  const signIn = async (email: string, password: string) => {
    const cred = await signInWithEmailAndPassword(auth, email, password);
    const token = await cred.user.getIdToken();
    setIdToken(token);
    setUser(cred.user);
    // Ensure user exists in backend DB
    try {
      await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idToken: token,
          displayName: cred.user.displayName ?? "",
          email: cred.user.email ?? "",
        }),
      });
    } catch (e) {
      console.warn("Backend register failed:", e);
    }
  };

  const signInWithGoogle = async () => {
    const cred = await signInWithPopup(auth, new GoogleAuthProvider());
    const token = await cred.user.getIdToken();
    setIdToken(token);
    setUser(cred.user);
    try {
      await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idToken: token,
          displayName: cred.user.displayName ?? "",
          email: cred.user.email ?? "",
        }),
      });
    } catch (e) {
      console.warn("Backend register failed:", e);
    }
  };

  const signOut = async () => {
    await firebaseSignOut(auth);
    setUser(null);
    setIdToken(null);
  };

  const getIdToken = async (): Promise<string | null> => {
    if (!user) return null;
    try {
      const token = await user.getIdToken(true);
      setIdToken(token);
      return token;
    } catch {
      return null;
    }
  };

  const updatePassword = async (currentPassword: string, newPassword: string) => {
    if (!user || !user.email) throw new Error("You must be signed in with email to change password.");
    const { EmailAuthProvider, reauthenticateWithCredential, updatePassword: firebaseUpdatePassword } = await import("firebase/auth");
    const credential = EmailAuthProvider.credential(user.email, currentPassword);
    await reauthenticateWithCredential(user, credential);
    await firebaseUpdatePassword(user, newPassword);
  };

  const updateDisplayName = async (displayName: string) => {
    if (!user) throw new Error("You must be signed in to update your name.");
    const name = displayName.trim();
    if (!name) throw new Error("Name cannot be empty.");
    await updateProfile(user, { displayName: name });
    const token = await user.getIdToken(true);
    setIdToken(token);
    try {
      const res = await fetch(`${API_BASE}/auth/profile`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken: token, displayName: name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string; error?: string }).detail || (err as { detail?: string; error?: string }).error || "Failed to update profile");
      }
    } catch (e) {
      if (e instanceof Error) throw e;
      throw new Error("Failed to update profile");
    }
    forceUpdate();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        idToken,
        getIdToken,
        loading,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        updatePassword,
        updateDisplayName,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
