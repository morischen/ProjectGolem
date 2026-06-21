"use client";

import { useState } from "react";
import { submitAppeal, type AppealType } from "../lib/gateway";

const TYPES: { value: AppealType; label: string }[] = [
  { value: "new_evidence", label: "New evidence" },
  { value: "source_challenge", label: "Challenge a source" },
  { value: "methodology", label: "Methodology concern" },
];

/**
 * Appeal-entry form (blueprint appeals process). Anyone may challenge a verdict;
 * the appeal is POSTed to the gateway's public route, lands in the review queue,
 * and is logged publicly — which we state here so the affordance sets expectations.
 */
export function AppealEntry({
  claimId = "demo-claim",
  onAppeal,
}: {
  claimId?: string;
  onAppeal?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [appealType, setAppealType] = useState<AppealType>("new_evidence");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await submitAppeal({ claimId, appealType, body: body.trim() });
      setStatus("sent");
      setBody("");
      onAppeal?.();
    } catch {
      setStatus("error");
    }
  }

  return (
    <section aria-label="appeal">
      <h3>Challenge this verdict</h3>
      <p>
        Submit new evidence, challenge a source, or raise a methodology concern.
        Every appeal is logged publicly.
      </p>
      {!open ? (
        <button
          type="button"
          aria-label="Submit an appeal"
          onClick={() => setOpen(true)}
        >
          Submit new evidence or an appeal
        </button>
      ) : (
        <form onSubmit={submit} aria-label="appeal form">
          <label>
            Type{" "}
            <select
              value={appealType}
              onChange={(e) => setAppealType(e.target.value as AppealType)}
              aria-label="appeal type"
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Details{" "}
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              aria-label="appeal details"
              required
            />
          </label>
          <button type="submit" disabled={body.trim().length === 0}>
            Send appeal
          </button>
        </form>
      )}
      {status === "sent" && (
        <p role="status">
          Appeal received — it will be reviewed and logged publicly.
        </p>
      )}
      {status === "error" && (
        <p role="alert">
          Could not submit your appeal. Please try again later.
        </p>
      )}
    </section>
  );
}
