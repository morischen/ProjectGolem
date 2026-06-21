import type { Verdict } from "@eip/contracts";

/**
 * A persisted, versioned verdict snapshot from the Trust Engine store
 * (eip_persistence.VerdictRecord, ADR-0008). Mirrors the Python model; there is
 * no generated contract for it yet, so it is declared here.
 */
export interface VerdictRecord {
  claim_id: string;
  version: number;
  verdict: Verdict;
  score: number;
  weights_version: string;
  knowledge_time: string;
  event_time: string | null;
  payload: Record<string, unknown>;
}

export interface ListClaimsInput {
  limit?: number;
  offset?: number;
}

/**
 * Read-only client for the Trust Engine's admin/browse surface. The gateway
 * proxies these for the admin portal (A1) under the `admin` scope; it never
 * mutates or scores (INV-DETERMINISM).
 */
export class AdminClient {
  constructor(private readonly baseUrl: string) {}

  async listClaims(input: ListClaimsInput = {}): Promise<VerdictRecord[]> {
    const params = new URLSearchParams();
    if (input.limit !== undefined) params.set("limit", String(input.limit));
    if (input.offset !== undefined) params.set("offset", String(input.offset));
    const qs = params.toString();
    return this.get<VerdictRecord[]>(`/v1/claims${qs ? `?${qs}` : ""}`);
  }

  async claimHistory(claimId: string): Promise<VerdictRecord[]> {
    return this.get<VerdictRecord[]>(
      `/v1/claims/${encodeURIComponent(claimId)}/verdicts`,
    );
  }

  async latestVerdict(claimId: string): Promise<VerdictRecord | null> {
    const res = await fetch(
      `${this.baseUrl}/v1/claims/${encodeURIComponent(claimId)}/verdict`,
    );
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as VerdictRecord;
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as T;
  }
}
