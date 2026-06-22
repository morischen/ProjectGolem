"use client";

import { useState } from "react";
import { submitClaim } from "../lib/gateway";

/**
 * Public "submit a claim for assessment" form. The claim enters the review queue
 * for triage — it is not scored on the spot (assessment is an authenticated
 * operation). Mirrors the appeals affordance.
 */
export function ClaimSubmit({ onSubmitted }: { onSubmitted?: () => void }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await submitClaim({ text: text.trim() });
      setStatus("sent");
      setText("");
      onSubmitted?.();
    } catch {
      setStatus("error");
    }
  }

  return (
    <section aria-label="submit a claim">
      <h3>Submit a claim for assessment</h3>
      <p>
        Propose a disputed claim for the platform to assess. Submissions are
        triaged by reviewers before assessment.
      </p>
      {!open ? (
        <button
          type="button"
          aria-label="Propose a claim"
          onClick={() => setOpen(true)}
        >
          Propose a claim
        </button>
      ) : (
        <form onSubmit={submit} aria-label="claim form">
          <label>
            Claim{" "}
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              aria-label="claim text"
              required
            />
          </label>
          <button type="submit" disabled={text.trim().length === 0}>
            Submit claim
          </button>
        </form>
      )}
      {status === "sent" && (
        <p role="status">Thanks — your claim has been queued for review.</p>
      )}
      {status === "error" && (
        <p role="alert">Could not submit your claim. Please try again later.</p>
      )}
    </section>
  );
}
