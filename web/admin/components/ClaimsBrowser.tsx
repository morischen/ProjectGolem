"use client";

import { useEffect, useState } from "react";
import {
  AdminApiError,
  claimHistory,
  listClaims,
  type VerdictRecord,
} from "../lib/adminApi";

/** Read-only claims list + drill-down to a claim's verdict history. */
export function ClaimsBrowser({
  apiKey,
  onAuthError,
}: {
  apiKey: string;
  onAuthError?: () => void;
}) {
  const [claims, setClaims] = useState<VerdictRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [history, setHistory] = useState<VerdictRecord[] | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    listClaims(apiKey)
      .then((rows) => {
        if (active) setClaims(rows);
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (
          err instanceof AdminApiError &&
          (err.status === 401 || err.status === 403)
        ) {
          onAuthError?.();
          setError("Access denied — check your admin API key.");
        } else {
          setError("Could not load claims.");
        }
      });
    return () => {
      active = false;
    };
  }, [apiKey, onAuthError]);

  function openClaim(claimId: string) {
    setSelected(claimId);
    setHistory(null);
    claimHistory(apiKey, claimId)
      .then(setHistory)
      .catch(() => setError("Could not load claim history."));
  }

  if (error) return <p role="alert">{error}</p>;
  if (claims === null) return <p>Loading claims…</p>;

  return (
    <main>
      <h1>Verdicts ({claims.length})</h1>
      {claims.length === 0 ? (
        <p>No verdicts recorded yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Claim</th>
              <th>Verdict</th>
              <th>Score</th>
              <th>Version</th>
              <th>Knowledge time</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((c) => (
              <tr key={c.claim_id}>
                <td>
                  <button type="button" onClick={() => openClaim(c.claim_id)}>
                    {c.claim_id}
                  </button>
                </td>
                <td>{c.verdict}</td>
                <td>{c.score.toFixed(2)}</td>
                <td>{c.version}</td>
                <td>{c.knowledge_time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selected && (
        <section aria-label={`history for ${selected}`}>
          <h2>History — {selected}</h2>
          {history === null ? (
            <p>Loading history…</p>
          ) : (
            <ol>
              {history.map((h) => (
                <li key={h.version}>
                  v{h.version}: {h.verdict} ({h.score.toFixed(2)}) @{" "}
                  {h.knowledge_time}
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </main>
  );
}
