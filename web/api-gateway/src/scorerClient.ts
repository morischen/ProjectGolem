import type { Evidence, TrustResult } from "@eip/contracts";

export interface ScoreInput {
  evidence: Evidence[];
  historical?: boolean;
  /** Persist the verdict under this claim id (Trust Engine store, ADR-0008). */
  claimId?: string;
  /** Graph-derived independence_ratio override (ADR-0007). */
  independence?: number | null;
  /** ISO-8601 time the underlying event occurred, if known. */
  eventTime?: string | null;
}

/**
 * Typed client for the Python Trust Engine's HTTP surface (POST /v1/score).
 * The gateway proxies scoring here; it never computes scores itself
 * (INV-DETERMINISM). The response shape is the generated `TrustResult` contract.
 */
export class ScorerClient {
  constructor(private readonly baseUrl: string) {}

  async score(input: ScoreInput): Promise<TrustResult> {
    const res = await fetch(`${this.baseUrl}/v1/score`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        evidence: input.evidence,
        historical: input.historical ?? false,
        ...(input.claimId !== undefined ? { claim_id: input.claimId } : {}),
        ...(input.independence != null
          ? { independence: input.independence }
          : {}),
        ...(input.eventTime != null ? { event_time: input.eventTime } : {}),
      }),
    });
    if (!res.ok) {
      throw new Error(`trust-engine responded ${res.status}`);
    }
    return (await res.json()) as TrustResult;
  }
}
