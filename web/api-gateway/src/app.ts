import Fastify, { type FastifyInstance } from "fastify";
import type { Verdict } from "@eip/contracts";

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

export function buildApp(): FastifyInstance {
  const app = Fastify({ logger: false });

  app.get("/health", async () => ({ status: "ok" }));

  app.get("/v1/info", async () => ({
    service: "api-gateway",
    role: "auth/routing/orchestration only — no scoring (INV-DETERMINISM)",
    verdicts: ALLOWED_VERDICTS,
  }));

  return app;
}
