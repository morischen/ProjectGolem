"use client";

import { useCallback, useState } from "react";
import { Login } from "../components/Login";
import { ClaimsBrowser } from "../components/ClaimsBrowser";
import { ConfigEditor } from "../components/ConfigEditor";
import { ReviewQueue } from "../components/ReviewQueue";

type Tab = "claims" | "config" | "review" | "appeals";

const TABS: { id: Tab; label: string }[] = [
  { id: "claims", label: "Claims" },
  { id: "review", label: "Review" },
  { id: "appeals", label: "Appeals" },
  { id: "config", label: "Config" },
];

export default function AdminPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("claims");
  const signOut = useCallback(() => setApiKey(null), []);

  if (apiKey === null) return <Login onSubmit={setApiKey} />;

  return (
    <>
      <nav aria-label="admin sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            aria-pressed={tab === t.id}
          >
            {t.label}
          </button>
        ))}
        <button type="button" onClick={signOut}>
          Sign out
        </button>
      </nav>
      {tab === "claims" && (
        <ClaimsBrowser apiKey={apiKey} onAuthError={signOut} />
      )}
      {tab === "review" && (
        <ReviewQueue apiKey={apiKey} mode="review" onAuthError={signOut} />
      )}
      {tab === "appeals" && (
        <ReviewQueue apiKey={apiKey} mode="appeals" onAuthError={signOut} />
      )}
      {tab === "config" && (
        <ConfigEditor apiKey={apiKey} onAuthError={signOut} />
      )}
    </>
  );
}
