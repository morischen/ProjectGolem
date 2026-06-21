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

/** The scoring-weights document stored in a config version's payload. */
export interface ScoringWeightsPayload {
  version: string;
  source_reliability: number;
  corroboration: number;
  evidence_quality: number;
  independence: number;
  freshness: number;
  tier_reliability: Record<string, number>;
  strength_floor: number;
  mixed_conflict_threshold: number;
  verified_threshold: number;
}

/** A versioned config snapshot (eip_persistence.ConfigRecord). */
export interface ConfigRecord {
  profile: string;
  version: number;
  payload: ScoringWeightsPayload;
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

export interface AuditEntry {
  id: number;
  actor: string;
  action: string;
  target: string;
  knowledge_time: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
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

/** Gateway base URL — client-side, so it must be NEXT_PUBLIC_*. */
const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:4000";

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: unknown,
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

/** Active scoring config per profile, via GET /admin/config. */
export function getConfig(apiKey: string): Promise<ConfigView> {
  return get<ConfigView>("/admin/config", apiKey);
}

/** Version history for one config profile (oldest → newest). */
export function configHistory(
  apiKey: string,
  profile: string,
): Promise<ConfigRecord[]> {
  return get<ConfigRecord[]>(
    `/admin/config/${encodeURIComponent(profile)}/history`,
    apiKey,
  );
}

/** Recent audit-log entries (newest first), via GET /admin/audit. */
export function listAudit(
  apiKey: string,
  opts: { limit?: number; target?: string } = {},
): Promise<AuditEntry[]> {
  const params = new URLSearchParams();
  if (opts.limit !== undefined) params.set("limit", String(opts.limit));
  if (opts.target !== undefined) params.set("target", opts.target);
  const qs = params.toString();
  return get<AuditEntry[]>(`/admin/audit${qs ? `?${qs}` : ""}`, apiKey);
}

/** Body of a guarded config edit (POST /admin/config). */
export interface ConfigUpdateBody {
  profile: string;
  actor: string;
  note?: string;
  source_reliability: number;
  corroboration: number;
  evidence_quality: number;
  independence: number;
  freshness: number;
  tier_reliability: Record<string, number>;
  strength_floor: number;
  mixed_conflict_threshold: number;
  verified_threshold: number;
}

/**
 * Submit a guarded config edit. Creates a new version server-side. A 422 (e.g.
 * weights not summing to 1.0) is surfaced as an AdminApiError carrying the detail,
 * so the form can show why the edit was rejected.
 */
export async function updateConfig(
  apiKey: string,
  body: ConfigUpdateBody,
): Promise<ConfigRecord> {
  const res = await fetch(`${GATEWAY_URL}/admin/config`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": apiKey },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new AdminApiError(
      `config update rejected (${res.status})`,
      res.status,
      (json as { detail?: unknown }).detail ?? json,
    );
  }
  return json as ConfigRecord;
}

/** Review-queue items (newest first), via GET /admin/review. */
export function listReview(
  apiKey: string,
  opts: { status?: string; limit?: number } = {},
): Promise<ReviewRecord[]> {
  const params = new URLSearchParams();
  if (opts.status !== undefined) params.set("status", opts.status);
  if (opts.limit !== undefined) params.set("limit", String(opts.limit));
  const qs = params.toString();
  return get<ReviewRecord[]>(`/admin/review${qs ? `?${qs}` : ""}`, apiKey);
}

/** Appeals (review items of kind 'appeal'), via GET /admin/appeals. */
export function listAppeals(apiKey: string): Promise<ReviewRecord[]> {
  return get<ReviewRecord[]>("/admin/appeals", apiKey);
}

/** A reviewer's decision on a queued item. */
export interface ResolveBody {
  reviewer: string;
  decision: "upheld" | "override" | "dismissed";
  note?: string;
  override_verdict?: string;
  override_score?: number;
}

/**
 * Resolve a review item. An 'override' appends a new, reviewer-attributed verdict
 * version server-side (INV-OVERRIDE). Engine rejections (404/409/422) are surfaced
 * as AdminApiError so the UI can explain them.
 */
export async function resolveReview(
  apiKey: string,
  itemId: number,
  body: ResolveBody,
): Promise<ReviewRecord> {
  const res = await fetch(`${GATEWAY_URL}/admin/review/${itemId}/resolve`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": apiKey },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new AdminApiError(
      `resolve rejected (${res.status})`,
      res.status,
      (json as { detail?: unknown }).detail ?? json,
    );
  }
  return json as ReviewRecord;
}
