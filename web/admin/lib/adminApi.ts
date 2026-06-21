import type { Verdict } from "@eip/contracts";

/**
 * A persisted, versioned verdict snapshot (eip_persistence.VerdictRecord, ADR-0008),
 * as returned by the gateway's admin proxies. No generated contract exists for it
 * yet, so it is mirrored here.
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

/** Gateway base URL — client-side, so it must be NEXT_PUBLIC_*. */
const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:4000";

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "AdminApiError";
  }
}

async function get<T>(path: string, apiKey: string): Promise<T> {
  const res = await fetch(`${GATEWAY_URL}${path}`, {
    headers: { "x-api-key": apiKey },
  });
  if (!res.ok) {
    throw new AdminApiError(`gateway responded ${res.status}`, res.status);
  }
  return (await res.json()) as T;
}

/** Latest verdict per claim (newest first), via GET /admin/claims. */
export function listClaims(
  apiKey: string,
  opts: { limit?: number; offset?: number } = {},
): Promise<VerdictRecord[]> {
  const params = new URLSearchParams();
  if (opts.limit !== undefined) params.set("limit", String(opts.limit));
  if (opts.offset !== undefined) params.set("offset", String(opts.offset));
  const qs = params.toString();
  return get<VerdictRecord[]>(`/admin/claims${qs ? `?${qs}` : ""}`, apiKey);
}

/** Full append-only verdict history for one claim (oldest → newest). */
export function claimHistory(
  apiKey: string,
  claimId: string,
): Promise<VerdictRecord[]> {
  return get<VerdictRecord[]>(
    `/admin/claims/${encodeURIComponent(claimId)}/verdicts`,
    apiKey,
  );
}
