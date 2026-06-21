"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AdminApiError,
  listAppeals,
  listReview,
  resolveReview,
  type ResolveBody,
  type ReviewRecord,
} from "../lib/adminApi";

const VERDICTS = [
  "Verified",
  "Likely True",
  "Mixed Evidence",
  "Insufficient Evidence",
  "Likely False",
  "False",
];

/**
 * The human-review surface. `mode="review"` shows the open escalation queue;
 * `mode="appeals"` shows public appeals. Both resolve via the same endpoint —
 * an override appends a new reviewer-attributed verdict version server-side.
 */
export function ReviewQueue({
  apiKey,
  mode = "review",
  onAuthError,
}: {
  apiKey: string;
  mode?: "review" | "appeals";
  onAuthError?: () => void;
}) {
  const [items, setItems] = useState<ReviewRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ReviewRecord | null>(null);

  const handleAuth = useCallback(
    (err: unknown): boolean => {
      if (
        err instanceof AdminApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        onAuthError?.();
        setError("Access denied — check your admin API key.");
        return true;
      }
      return false;
    },
    [onAuthError],
  );

  const load = useCallback(async () => {
    setError(null);
    try {
      const rows =
        mode === "appeals"
          ? await listAppeals(apiKey)
          : await listReview(apiKey, { status: "open" });
      setItems(rows);
    } catch (err: unknown) {
      if (!handleAuth(err)) setError("Could not load the queue.");
    }
  }, [apiKey, mode, handleAuth]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error && !items) return <p role="alert">{error}</p>;
  if (items === null) return <p>Loading…</p>;

  return (
    <main>
      <h1>{mode === "appeals" ? "Appeals" : "Review queue"}</h1>
      {items.length === 0 ? (
        <p>Nothing {mode === "appeals" ? "appealed" : "to review"}.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Claim</th>
              <th>Kind</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id}>
                <td>{it.id}</td>
                <td>{it.claim_id}</td>
                <td>{it.kind}</td>
                <td>{it.status}</td>
                <td>{it.created_time}</td>
                <td>
                  {it.status === "open" && (
                    <button type="button" onClick={() => setSelected(it)}>
                      Resolve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {error && <p role="alert">{error}</p>}

      {selected && (
        <ResolvePanel
          apiKey={apiKey}
          item={selected}
          onClose={() => setSelected(null)}
          onResolved={() => {
            setSelected(null);
            void load();
          }}
          onAuthError={handleAuth}
        />
      )}
    </main>
  );
}

function ResolvePanel({
  apiKey,
  item,
  onClose,
  onResolved,
  onAuthError,
}: {
  apiKey: string;
  item: ReviewRecord;
  onClose: () => void;
  onResolved: () => void;
  onAuthError: (err: unknown) => boolean;
}) {
  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState<ResolveBody["decision"]>("upheld");
  const [overrideVerdict, setOverrideVerdict] = useState(VERDICTS[0]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canSubmit = reviewer.trim().length > 0;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await resolveReview(apiKey, item.id, {
        reviewer: reviewer.trim(),
        decision,
        note: note.trim() || undefined,
        override_verdict: decision === "override" ? overrideVerdict : undefined,
      });
      onResolved();
    } catch (err: unknown) {
      if (onAuthError(err)) return;
      setError("Could not resolve this item.");
    }
  }

  return (
    <section aria-label={`resolve item ${item.id}`}>
      <h2>
        Resolve #{item.id} — claim {item.claim_id} ({item.kind})
      </h2>
      {item.detail && Object.keys(item.detail).length > 0 && (
        <pre>{JSON.stringify(item.detail, null, 2)}</pre>
      )}
      <form onSubmit={submit} aria-label="resolve form">
        <label>
          Your name{" "}
          <input
            value={reviewer}
            onChange={(e) => setReviewer(e.target.value)}
            aria-label="reviewer"
            required
          />
        </label>
        <label>
          Decision{" "}
          <select
            value={decision}
            onChange={(e) =>
              setDecision(e.target.value as ResolveBody["decision"])
            }
            aria-label="decision"
          >
            <option value="upheld">upheld</option>
            <option value="override">override</option>
            <option value="dismissed">dismissed</option>
          </select>
        </label>
        {decision === "override" && (
          <label>
            Override verdict{" "}
            <select
              value={overrideVerdict}
              onChange={(e) => setOverrideVerdict(e.target.value)}
              aria-label="override verdict"
            >
              {VERDICTS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Note{" "}
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            aria-label="resolve note"
          />
        </label>
        <button type="submit" disabled={!canSubmit}>
          Submit decision
        </button>
        <button type="button" onClick={onClose}>
          Cancel
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
