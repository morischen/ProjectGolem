"use client";

import { useCallback, useState } from "react";
import { Login } from "../components/Login";
import { ClaimsBrowser } from "../components/ClaimsBrowser";

export default function AdminPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const signOut = useCallback(() => setApiKey(null), []);

  if (apiKey === null) return <Login onSubmit={setApiKey} />;
  return <ClaimsBrowser apiKey={apiKey} onAuthError={signOut} />;
}
