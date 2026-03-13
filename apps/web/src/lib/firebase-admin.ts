import { initializeApp, cert, getApps, App } from "firebase-admin/app";
import { getFirestore, Firestore } from "firebase-admin/firestore";

let adminApp: App | null = null;
let adminDb: Firestore | null = null;

/**
 * Initialize Firebase Admin SDK for server-side operations.
 * Ensures singleton pattern - only initializes once.
 */
function getAdminApp(): App {
  if (adminApp) {
    return adminApp;
  }

  // Check if already initialized
  const existingApps = getApps();
  if (existingApps.length > 0) {
    adminApp = existingApps[0];
    return adminApp;
  }

  const serviceAccount = process.env.FIREBASE_ADMIN_SERVICE_ACCOUNT;
  if (!serviceAccount) {
    throw new Error(
      "FIREBASE_ADMIN_SERVICE_ACCOUNT environment variable is not set"
    );
  }

  try {
    const serviceAccountJSON = JSON.parse(serviceAccount);
    adminApp = initializeApp({
      credential: cert(serviceAccountJSON),
    });
    return adminApp;
  } catch (error) {
    throw new Error(
      `Failed to initialize Firebase Admin: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
}

/**
 * Get Firestore Admin instance for server-side database operations.
 * @returns Firestore instance
 */
export function getAdminDb(): Firestore {
  if (adminDb) {
    return adminDb;
  }

  const app = getAdminApp();
  adminDb = getFirestore(app);
  return adminDb;
}

/**
 * Verify a Firebase ID token and return the decoded token.
 * @param idToken - The Firebase ID token to verify
 * @returns The decoded token containing user information
 */
export async function verifyIdToken(idToken: string) {
  const { getAuth } = await import("firebase-admin/auth");
  const auth = getAuth(getAdminApp());
  return auth.verifyIdToken(idToken);
}
