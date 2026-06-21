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

/** A versioned config snapshot (eip_persistence.ConfigRecord). */
export interface ConfigRecord {
  profile: string;
  version: number;
  payload: Record<string, unknown>;
  knowledge_time: string;
  actor: string | null;
  note: string | null;
}

export interface ProfileConfig {
  profile: string;
  active: ConfigRecord;
  versions: number[];
}

export interface ConfigView {
  profiles: ProfileConfig[];
}

/** Result of a config write: the Trust Engine status (e.g. 422 on sum-to-1) + body. */
export interface ConfigWriteResult {
  status: number;
  body: unknown;
}

/** A human-review queue item (eip_persistence.ReviewRecord). */
export interface ReviewRecord {
  id: number;
  claim_id: string;
  kind: string;
  status: string;
  created_time: string;
  detail: Record<string, unknown>;
  resolution: Record<string, unknown> | null;
  resolved_time: string | null;
}

/** Result of a review/appeal write: the engine status (404/409/422) + body. */
export interface WriteResult {
  status: number;
  body: unknown;
}

export interface ListReviewInput {
  status?: string;
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

  async getConfig(): Promise<ConfigView> {
    return this.get<ConfigView>("/v1/config");
  }

  async configHistory(profile: string): Promise<ConfigRecord[]> {
    return this.get<ConfigRecord[]>(
      `/v1/config/${encodeURIComponent(profile)}/history`,
    );
  }

  /**
   * Forward a config edit to the Trust Engine. Validation failures (sum-to-1,
   * ranges) come back as 422 — preserved here so the caller can pass them through,
   * rather than collapsing to a generic error.
   */
  async updateConfig(body: unknown): Promise<ConfigWriteResult> {
    const res = await fetch(`${this.baseUrl}/v1/config`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    return { status: res.status, body: await res.json() };
  }

  async listAudit(
    input: ListClaimsInput & { target?: string } = {},
  ): Promise<Record<string, unknown>[]> {
    const params = new URLSearchParams();
    if (input.limit !== undefined) params.set("limit", String(input.limit));
    if (input.offset !== undefined) params.set("offset", String(input.offset));
    if (input.target !== undefined) params.set("target", input.target);
    const qs = params.toString();
    return this.get<Record<string, unknown>[]>(
      `/v1/audit${qs ? `?${qs}` : ""}`,
    );
  }

  async listReview(input: ListReviewInput = {}): Promise<ReviewRecord[]> {
    const params = new URLSearchParams();
    if (input.status !== undefined) params.set("status", input.status);
    if (input.limit !== undefined) params.set("limit", String(input.limit));
    if (input.offset !== undefined) params.set("offset", String(input.offset));
    const qs = params.toString();
    return this.get<ReviewRecord[]>(`/v1/review${qs ? `?${qs}` : ""}`);
  }

  async getReview(itemId: number): Promise<ReviewRecord | null> {
    const res = await fetch(`${this.baseUrl}/v1/review/${itemId}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as ReviewRecord;
  }

  /** Resolve a review item. Preserves the engine status (404/409/422) for the caller. */
  async resolveReview(itemId: number, body: unknown): Promise<WriteResult> {
    const res = await fetch(`${this.baseUrl}/v1/review/${itemId}/resolve`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    return { status: res.status, body: await res.json() };
  }

  async getMetrics(): Promise<Record<string, unknown>> {
    return this.get<Record<string, unknown>>("/v1/metrics");
  }

  async listCalibrationRuns(): Promise<Record<string, unknown>[]> {
    return this.get<Record<string, unknown>[]>("/v1/calibration/runs");
  }

  /** Trigger a benchmark run and append it to the calibration ledger. */
  async recordCalibrationRun(): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/calibration/runs`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as Record<string, unknown>;
  }

  /** Best-effort: record an admin action (e.g. key management) in the audit log. */
  async recordAudit(entry: {
    actor: string;
    action: string;
    target: string;
    before?: Record<string, unknown> | null;
    after?: Record<string, unknown> | null;
  }): Promise<void> {
    await fetch(`${this.baseUrl}/v1/audit`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(entry),
    });
  }

  async listAppeals(
    input: { limit?: number; offset?: number } = {},
  ): Promise<ReviewRecord[]> {
    const params = new URLSearchParams();
    if (input.limit !== undefined) params.set("limit", String(input.limit));
    if (input.offset !== undefined) params.set("offset", String(input.offset));
    const qs = params.toString();
    return this.get<ReviewRecord[]>(`/v1/appeals${qs ? `?${qs}` : ""}`);
  }

  /** Submit a public appeal. Preserves the engine status (e.g. 422 invalid type). */
  async submitAppeal(body: unknown): Promise<WriteResult> {
    const res = await fetch(`${this.baseUrl}/v1/appeals`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    return { status: res.status, body: await res.json() };
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as T;
  }
}
