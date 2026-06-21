import Fastify, {
  type FastifyInstance,
  type preHandlerHookHandler,
} from "fastify";
import type { Evidence, Verdict } from "@eip/contracts";
import { ScorerClient } from "./scorerClient";
import { ClaimClient } from "./claimClient";
import { EvidenceClient } from "./evidenceClient";
import { AdminClient } from "./adminClient";
import {
  type ApiKeyMap,
  KeyStore,
  loadApiKeysFromEnv,
  requireScope,
} from "./auth";
import { type RateLimitOptions, rateLimitHook } from "./rateLimit";

// The six allowed verdicts, typed against the generated contract (drift fails the
// typecheck). The gateway is presentation/orchestration only — it never scores
// (INV-DETERMINISM); scoring lives in the Python Trust Engine.
const ALLOWED_VERDICTS: Verdict[] = [
  "Verified",
  "Likely True",
  "Mixed Evidence",
  "Insufficient Evidence",
  "Likely False",
  "False",
];

export interface AppOptions {
  scorer?: ScorerClient;
  claim?: ClaimClient;
  evidence?: EvidenceClient;
  /** Read-only browse client for the admin portal (Trust Engine store). */
  admin?: AdminClient;
  /** API keys → scopes. Empty/omitted → auth disabled (dev). Default: from env. */
  apiKeys?: ApiKeyMap;
  /** Managed key store. Default: a KeyStore seeded from `apiKeys`. */
  keyStore?: KeyStore;
  /** Rate-limit config, or null to disable. Default: 120 requests / 60s. */
  rateLimit?: RateLimitOptions | null;
}

interface ScoreBody {
  evidence?: Evidence[];
  historical?: boolean;
  claim_id?: string;
  independence?: number | null;
  event_time?: string | null;
}

interface ExtractBody {
  text?: string;
  claim_id?: string;
}

interface GatherBody {
  claim_text?: string;
  candidates?: unknown[];
}

interface AssessBody {
  text?: string;
  claim_id?: string;
  candidates?: unknown[];
  /** Citation edges (a cites b) for graph-derived independence (ADR-0007). */
  citations?: [string, string][];
  historical?: boolean;
  event_time?: string | null;
}

export function buildApp(opts: AppOptions = {}): FastifyInstance {
  const scorer =
    opts.scorer ??
    new ScorerClient(process.env.TRUST_ENGINE_URL ?? "http://localhost:8000");
  const claim =
    opts.claim ??
    new ClaimClient(process.env.CLAIM_ENGINE_URL ?? "http://localhost:8001");
  const evidence =
    opts.evidence ??
    new EvidenceClient(
      process.env.EVIDENCE_ENGINE_URL ?? "http://localhost:8002",
    );
  const admin =
    opts.admin ??
    new AdminClient(process.env.TRUST_ENGINE_URL ?? "http://localhost:8000");

  const keyStore =
    opts.keyStore ?? new KeyStore(opts.apiKeys ?? loadApiKeysFromEnv());
  const rateLimitOpts =
    opts.rateLimit === null
      ? null
      : (opts.rateLimit ?? { limit: 120, windowMs: 60_000 });

  // preHandlers for protected proxy routes: rate-limit, then require the scope.
  const protect = (scope: string): preHandlerHookHandler[] => {
    const handlers: preHandlerHookHandler[] = [];
    if (rateLimitOpts) handlers.push(rateLimitHook(rateLimitOpts));
    handlers.push(requireScope(keyStore, scope));
    return handlers;
  };

  // Public routes still get rate-limited (abuse control) but require no API key.
  const publicLimited = (): preHandlerHookHandler[] =>
    rateLimitOpts ? [rateLimitHook(rateLimitOpts)] : [];

  const app = Fastify({ logger: false });

  app.get("/health", async () => ({ status: "ok" }));

  app.get("/v1/info", async () => ({
    service: "api-gateway",
    role: "auth/routing/orchestration only — no scoring (INV-DETERMINISM)",
    verdicts: ALLOWED_VERDICTS,
  }));

  // Proxy scoring to the Trust Engine. The gateway validates and forwards; it does
  // not score. The returned shape is the Trust Engine's TrustResult contract.
  app.post(
    "/v1/score",
    { preHandler: protect("write") },
    async (request, reply) => {
      const body = (request.body ?? {}) as ScoreBody;
      if (!Array.isArray(body.evidence)) {
        reply.code(400);
        return { error: "body.evidence (array) is required" };
      }
      try {
        return await scorer.score({
          evidence: body.evidence,
          historical: body.historical,
          claimId: body.claim_id,
          independence: body.independence,
          eventTime: body.event_time,
        });
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  // Proxy claim extraction to the Claim Engine. Validates and forwards; the LLM
  // runs in the Python service, never here.
  app.post(
    "/v1/extract",
    { preHandler: protect("write") },
    async (request, reply) => {
      const body = (request.body ?? {}) as ExtractBody;
      if (typeof body.text !== "string" || typeof body.claim_id !== "string") {
        reply.code(400);
        return { error: "body.text and body.claim_id (strings) are required" };
      }
      try {
        return await claim.extract({ text: body.text, claimId: body.claim_id });
      } catch {
        reply.code(502);
        return { error: "claim-engine unavailable" };
      }
    },
  );

  // Proxy evidence gathering to the Evidence Engine. Validates and forwards; the
  // LLM classification runs in the Python service, never here.
  app.post(
    "/v1/gather",
    { preHandler: protect("write") },
    async (request, reply) => {
      const body = (request.body ?? {}) as GatherBody;
      if (
        typeof body.claim_text !== "string" ||
        !Array.isArray(body.candidates)
      ) {
        reply.code(400);
        return {
          error:
            "body.claim_text (string) and body.candidates (array) are required",
        };
      }
      try {
        return await evidence.gather({
          claimText: body.claim_text,
          candidates: body.candidates,
        });
      } catch {
        reply.code(502);
        return { error: "evidence-engine unavailable" };
      }
    },
  );

  // End-to-end assessment: extract -> gather -> score (+ persist), in one call. The
  // gateway only orchestrates the three engines (INV-DETERMINISM: it never scores);
  // the verdict is produced by the Trust Engine and persisted there (INV-TEMPORAL).
  app.post(
    "/v1/assess",
    { preHandler: protect("write") },
    async (request, reply) => {
      const body = (request.body ?? {}) as AssessBody;
      if (typeof body.text !== "string" || typeof body.claim_id !== "string") {
        reply.code(400);
        return { error: "body.text and body.claim_id (strings) are required" };
      }
      const candidates = Array.isArray(body.candidates) ? body.candidates : [];
      try {
        const claimObj = await claim.extract({
          text: body.text,
          claimId: body.claim_id,
        });
        const ev = await evidence.gather({
          claimText: claimObj.text,
          candidates,
        });
        // When citations are supplied, derive the graph-based independence_ratio and
        // pass it as a scoring override (ADR-0007); otherwise the Trust Engine uses
        // its built-in count heuristic.
        let independence: number | undefined;
        if (Array.isArray(body.citations) && body.citations.length > 0) {
          const sourceIds = ev.map((e) => e.source_id);
          const report = await evidence.independence({
            sourceIds,
            citations: body.citations,
          });
          independence = report.independence_ratio;
        }
        const result = await scorer.score({
          evidence: ev,
          historical: body.historical,
          claimId: body.claim_id,
          eventTime: body.event_time,
          independence,
        });
        return { claim: claimObj, evidence: ev, result };
      } catch {
        reply.code(502);
        return { error: "assessment pipeline unavailable" };
      }
    },
  );

  // Admin browse surface (read-only). Proxies the Trust Engine store under the
  // `admin` scope for the admin portal (A1). Never mutates or scores.
  app.get(
    "/admin/claims",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const q = (request.query ?? {}) as { limit?: string; offset?: string };
      const limit = q.limit !== undefined ? Number(q.limit) : undefined;
      const offset = q.offset !== undefined ? Number(q.offset) : undefined;
      try {
        return await admin.listClaims({ limit, offset });
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/claims/:id/verdicts",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      try {
        return await admin.claimHistory(id);
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/claims/:id/verdict",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      try {
        const record = await admin.latestVerdict(id);
        if (record === null) {
          reply.code(404);
          return { error: "no verdict for claim" };
        }
        return record;
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  // Scoring-config governance (A2): view + guarded, audited edit. The gateway
  // forwards only; the Trust Engine owns versioning, validation, and the audit log.
  app.get(
    "/admin/config",
    { preHandler: protect("admin") },
    async (_request, reply) => {
      try {
        return await admin.getConfig();
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/config/:profile/history",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { profile } = request.params as { profile: string };
      try {
        return await admin.configHistory(profile);
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.post(
    "/admin/config",
    { preHandler: protect("admin") },
    async (request, reply) => {
      try {
        const result = await admin.updateConfig(request.body ?? {});
        reply.code(result.status); // preserve 200 / 422 from the engine
        return result.body;
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/audit",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const q = (request.query ?? {}) as {
        limit?: string;
        offset?: string;
        target?: string;
      };
      try {
        return await admin.listAudit({
          limit: q.limit !== undefined ? Number(q.limit) : undefined,
          offset: q.offset !== undefined ? Number(q.offset) : undefined,
          target: q.target,
        });
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  // Human review queue & appeals (A3). Admin reviewers list/inspect/resolve; the
  // gateway forwards only — the override→new-verdict-version logic lives in the
  // Trust Engine (INV-OVERRIDE/INV-DETERMINISM).
  app.get(
    "/admin/review",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const q = (request.query ?? {}) as {
        status?: string;
        limit?: string;
        offset?: string;
      };
      try {
        return await admin.listReview({
          status: q.status,
          limit: q.limit !== undefined ? Number(q.limit) : undefined,
          offset: q.offset !== undefined ? Number(q.offset) : undefined,
        });
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/review/:id",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      try {
        const item = await admin.getReview(Number(id));
        if (item === null) {
          reply.code(404);
          return { error: "no such review item" };
        }
        return item;
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.post(
    "/admin/review/:id/resolve",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      try {
        const result = await admin.resolveReview(
          Number(id),
          request.body ?? {},
        );
        reply.code(result.status); // preserve 200 / 404 / 409 / 422
        return result.body;
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  app.get(
    "/admin/appeals",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const q = (request.query ?? {}) as { limit?: string; offset?: string };
      try {
        return await admin.listAppeals({
          limit: q.limit !== undefined ? Number(q.limit) : undefined,
          offset: q.offset !== undefined ? Number(q.offset) : undefined,
        });
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  // Calibration / queue-health metrics for the admin dashboard (A4).
  app.get(
    "/admin/metrics",
    { preHandler: protect("admin") },
    async (_request, reply) => {
      try {
        return await admin.getMetrics();
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  // Access management (A4): managed API keys with admin CRUD. Key material lives in
  // the gateway (auth boundary); changes are mirrored into the Trust Engine audit log.
  app.get("/admin/keys", { preHandler: protect("admin") }, async () =>
    keyStore.list(),
  );

  app.post(
    "/admin/keys",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const body = (request.body ?? {}) as {
        label?: string;
        scopes?: unknown;
      };
      if (typeof body.label !== "string" || !Array.isArray(body.scopes)) {
        reply.code(400);
        return {
          error: "body.label (string) and body.scopes (array) required",
        };
      }
      const scopes = body.scopes.filter(
        (s): s is string => typeof s === "string",
      );
      const { plaintext, meta } = keyStore.create({
        label: body.label,
        scopes,
      });
      // Audit is best-effort: never block key creation if the engine is down.
      try {
        await admin.recordAudit({
          actor: "admin",
          action: "key.create",
          target: `key:${meta.id}`,
          after: {
            label: meta.label,
            scopes: meta.scopes,
            prefix: meta.prefix,
          },
        });
      } catch {
        /* audit is best-effort */
      }
      reply.code(201);
      // The plaintext is returned exactly once.
      return { key: plaintext, meta };
    },
  );

  app.post(
    "/admin/keys/:id/disable",
    { preHandler: protect("admin") },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const meta = keyStore.disable(id);
      if (meta === undefined) {
        reply.code(404);
        return { error: "no such key" };
      }
      try {
        await admin.recordAudit({
          actor: "admin",
          action: "key.disable",
          target: `key:${id}`,
          after: { disabled: true },
        });
      } catch {
        /* audit is best-effort */
      }
      return meta;
    },
  );

  // Public appeal submission — no API key, but rate-limited. Anyone may challenge a
  // verdict; the appeal lands in the review queue and is logged publicly.
  app.post(
    "/v1/appeals",
    { preHandler: publicLimited() },
    async (request, reply) => {
      try {
        const result = await admin.submitAppeal(request.body ?? {});
        reply.code(result.status); // preserve 200 / 422
        return result.body;
      } catch {
        reply.code(502);
        return { error: "trust-engine unavailable" };
      }
    },
  );

  return app;
}
