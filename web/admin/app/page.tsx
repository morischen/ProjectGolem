"use client";

import { useCallback, useState } from "react";
import { Login } from "../components/Login";
import { ClaimsBrowser } from "../components/ClaimsBrowser";
import { ConfigEditor } from "../components/ConfigEditor";

type Tab = "claims" | "config";

export default function AdminPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("claims");
  const signOut = useCallback(() => setApiKey(null), []);

  if (apiKey === null) return <Login onSubmit={setApiKey} />;

  return (
    <>
      <nav aria-label="admin sections">
        <button
          type="button"
          onClick={() => setTab("claims")}
          aria-pressed={tab === "claims"}
        >
          Claims
        </button>
        <button
          type="button"
          onClick={() => setTab("config")}
          aria-pressed={tab === "config"}
        >
          Config
        </button>
        <button type="button" onClick={signOut}>
          Sign out
        </button>
      </nav>
      {tab === "claims" ? (
        <ClaimsBrowser apiKey={apiKey} onAuthError={signOut} />
      ) : (
        <ConfigEditor apiKey={apiKey} onAuthError={signOut} />
      )}
    </>
  );
}
