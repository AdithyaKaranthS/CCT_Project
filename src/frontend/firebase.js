import { initializeApp } from "@firebase/app";
import { getAuth } from "@firebase/auth";

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const isFirebaseConfigured = [
  config.apiKey,
  config.authDomain,
  config.projectId,
  config.messagingSenderId,
  config.appId,
].every((value) => typeof value === "string" && value.length > 0 && !value.startsWith("your-"));
export const auth = isFirebaseConfigured ? getAuth(initializeApp(config)) : null;
