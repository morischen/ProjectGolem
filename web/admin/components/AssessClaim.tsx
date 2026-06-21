"use client";

import { useState } from "react";
import { AdminApiError, assess, type AssessResult } from "../lib/adminApi";

/**
 * Drive the end-to-end pipeline (POST /v1/assess) from claim text + optional
 * evidence candidates, and render the resulting verdict, breakdown, and evidence.
 * Needs a `write`-scoped key.
 */
export function AssessClaim({
  apiKey,
  onAuthError,
}: {
  apiKey: string;
  onAuthError?: () => void;
}) {
  const [text, setText] = useState("");
  const [claimId, setClaimId] = useState("");
  const [candidatesJson, setCandidatesJson] = useState("[]");
  const [citationsJson, setCitationsJson] = useState("[]");
  const [result, setResult] = useState<AssessResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const canSubmit =
    text.trim().length > 0 && claimId.trim().length > 0 && !busy;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    let candidates: unknown[];
    try {
      const parsed = JSON.parse(candidatesJson || "[]");
      if (!Array.isArray(parsed)) throw new Error("not an array");
      candidates = parsed;
    } catch {
      setError("Candidates must be a JSON array.");
      return;
    }

    let citations: [string, string][];
    try {
      const parsed = JSON.parse(citationsJson || "[]");
      if (!Array.isArray(parsed)) throw new Error("not an array");
      citations = parsed as [string, string][];
    } catch {
      setError("Citations must be a JSON array of [from, to] pairs.");
      return;
    }

    setBusy(true);
    try {
      const res = await assess(apiKey, {
        text: text.trim(),
        claim_id: claimId.trim(),
        candidates,
        citations,
      });
      setResult(res);
    } catch (err: unknown) {
      if (
        err instanceof AdminApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        onAuthError?.();
        setError("Access denied — this needs a write-scoped key.");
      } else {
        setError("Assessment failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Assess a claim</h1>
      <p>Runs extract → gather → score and persists a versioned verdict.</p>

      <form onSubmit={submit} aria-label="assess form">
        <label>
          Claim id{" "}
          <input
            value={claimId}
            onChange={(e) => setClaimId(e.target.value)}
            aria-label="claim id"
            required
          />
        </label>
        <label>
          Claim text{" "}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="claim text"
            required
          />
        </label>
        <label>
          Evidence candidates (JSON array){" "}
          <textarea
            value={candidatesJson}
            onChange={(e) => setCandidatesJson(e.target.value)}
            aria-label="candidates json"
          />
        </label>
        <label>
          Citations — JSON array of [from, to] pairs (independence){" "}
          <textarea
            value={citationsJson}
            onChange={(e) => setCitationsJson(e.target.value)}
            aria-label="citations json"
          />
        </label>
        <button type="submit" disabled={!canSubmit}>
          {busy ? "Assessing…" : "Assess"}
        </button>
      </form>

      {error && <p role="alert">{error}</p>}

      {result && (
        <section aria-label="assessment result">
          <h2>
            Verdict: {result.result.verdict} ({result.result.score.toFixed(2)})
          </h2>
          {result.result.weights_version && (
            <p>
              <small>config: {result.result.weights_version}</small>
            </p>
          )}
          {result.result.breakdown && (
            <dl>
              {Object.entries(result.result.breakdown).map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{Number(v).toFixed(3)}</dd>
                </div>
              ))}
            </dl>
          )}
          <h3>Evidence ({result.evidence.length})</h3>
          <ul>
            {result.evidence.map((ev, i) => (
              <li key={(ev.id as string) ?? i}>
                {String(ev.source_id ?? "?")} — {String(ev.relation ?? "?")}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
