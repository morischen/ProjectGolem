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

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) throw new Error(`trust-engine responded ${res.status}`);
    return (await res.json()) as T;
  }
}
