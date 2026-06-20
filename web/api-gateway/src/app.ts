import Fastify, { type FastifyInstance } from "fastify";
import type { Evidence, Verdict } from "@eip/contracts";
import { ScorerClient } from "./scorerClient";

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
}

interface ScoreBody {
  evidence?: Evidence[];
  historical?: boolean;
}

export function buildApp(opts: AppOptions = {}): FastifyInstance {
  const scorer =
    opts.scorer ??
    new ScorerClient(process.env.TRUST_ENGINE_URL ?? "http://localhost:8000");

  const app = Fastify({ logger: false });

  app.get("/health", async () => ({ status: "ok" }));

  app.get("/v1/info", async () => ({
    service: "api-gateway",
    role: "auth/routing/orchestration only — no scoring (INV-DETERMINISM)",
    verdicts: ALLOWED_VERDICTS,
  }));

  // Proxy scoring to the Trust Engine. The gateway validates and forwards; it does
  // not score. The returned shape is the Trust Engine's TrustResult contract.
  app.post("/v1/score", async (request, reply) => {
    const body = (request.body ?? {}) as ScoreBody;
    if (!Array.isArray(body.evidence)) {
      reply.code(400);
      return { error: "body.evidence (array) is required" };
    }
    try {
      return await scorer.score({
        evidence: body.evidence,
        historical: body.historical,
      });
    } catch {
      reply.code(502);
      return { error: "trust-engine unavailable" };
    }
  });

  return app;
}
