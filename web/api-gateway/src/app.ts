import Fastify, {
  type FastifyInstance,
  type preHandlerHookHandler,
} from "fastify";
import type { Evidence, Verdict } from "@eip/contracts";
import { ScorerClient } from "./scorerClient";
import { ClaimClient } from "./claimClient";
import { EvidenceClient } from "./evidenceClient";
import { AdminClient } from "./adminClient";
import { type ApiKeyMap, loadApiKeysFromEnv, requireScope } from "./auth";
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

  const apiKeys = opts.apiKeys ?? loadApiKeysFromEnv();
  const rateLimitOpts =
    opts.rateLimit === null
      ? null
      : (opts.rateLimit ?? { limit: 120, windowMs: 60_000 });

  // preHandlers for protected proxy routes: rate-limit, then require the scope.
  const protect = (scope: string): preHandlerHookHandler[] => {
    const handlers: preHandlerHookHandler[] = [];
    if (rateLimitOpts) handlers.push(rateLimitHook(rateLimitOpts));
    handlers.push(requireScope(apiKeys, scope));
    return handlers;
  };

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

  return app;
}
