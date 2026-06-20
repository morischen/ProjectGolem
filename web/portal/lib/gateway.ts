import type { Evidence, TrustResult } from "@eip/contracts";

import { sampleEvidence, sampleResult } from "./sample";

const GATEWAY_URL = process.env.GATEWAY_URL ?? "http://localhost:3000";

export interface VerdictView {
  result: TrustResult;
  evidence: Evidence[];
  /** true when the result came from the live gateway, false when using the static fallback. */
  live: boolean;
}

/**
 * Fetch a verdict from the gateway (`POST /v1/score`). Falls back to static sample
 * data when the gateway is unreachable or errors, so the portal renders (and tests
 * / `next build` stay hermetic) without a running backend.
 */
export async function fetchVerdict(
  evidence: Evidence[] = sampleEvidence,
): Promise<VerdictView> {
  try {
    const res = await fetch(`${GATEWAY_URL}/v1/score`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ evidence }),
    });
    if (!res.ok) {
      throw new Error(`gateway responded ${res.status}`);
    }
    const result = (await res.json()) as TrustResult;
    return { result, evidence, live: true };
  } catch {
    return { result: sampleResult, evidence: sampleEvidence, live: false };
  }
}
