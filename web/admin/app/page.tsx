"use client";

import { useCallback, useState } from "react";
import { Login } from "../components/Login";
import { ClaimsBrowser } from "../components/ClaimsBrowser";
import { ConfigEditor } from "../components/ConfigEditor";
import { ReviewQueue } from "../components/ReviewQueue";
import { Dashboard } from "../components/Dashboard";
import { AccessManagement } from "../components/AccessManagement";
import { AssessClaim } from "../components/AssessClaim";

type Tab =
  | "dashboard"
  | "assess"
  | "claims"
  | "config"
  | "review"
  | "appeals"
  | "access";

const TABS: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "assess", label: "Assess" },
  { id: "claims", label: "Claims" },
  { id: "review", label: "Review" },
  { id: "appeals", label: "Appeals" },
  { id: "config", label: "Config" },
  { id: "access", label: "Access" },
];

export default function AdminPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("dashboard");
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
      {tab === "dashboard" && (
        <Dashboard apiKey={apiKey} onAuthError={signOut} />
      )}
      {tab === "assess" && (
        <AssessClaim apiKey={apiKey} onAuthError={signOut} />
      )}
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
      {tab === "access" && (
        <AccessManagement apiKey={apiKey} onAuthError={signOut} />
      )}
    </>
  );
}
