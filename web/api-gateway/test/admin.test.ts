import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app";
import type { AdminClient, VerdictRecord } from "../src/adminClient";

const RECORD: VerdictRecord = {
  claim_id: "c1",
  version: 2,
  verdict: "Verified",
  score: 0.92,
  weights_version: "v0",
  knowledge_time: "2024-12-01T00:00:00Z",
  event_time: null,
  payload: {},
};

const CONFIG_VIEW = {
  profiles: [
    {
      profile: "default",
      active: {
        profile: "default",
        version: 1,
        payload: { freshness: 0.1 },
        knowledge_time: "2024-01-01T00:00:00Z",
        actor: "system",
        note: "seed",
      },
      versions: [1],
    },
  ],
};

const REVIEW_ITEM = {
  id: 1,
  claim_id: "c1",
  kind: "evidence_conflict",
  status: "open",
  created_time: "2024-01-01T00:00:00Z",
  detail: { score: 0.5 },
  resolution: null,
  resolved_time: null,
};

// A fake AdminClient so the routes are exercised without a live Trust Engine.
function fakeAdmin(overrides: Partial<AdminClient> = {}): AdminClient {
  return {
    listClaims: async () => [RECORD],
    claimHistory: async () => [RECORD],
    latestVerdict: async () => RECORD,
    getConfig: async () => CONFIG_VIEW,
    configHistory: async () =>
      CONFIG_VIEW.profiles[0].versions.map(
        () => CONFIG_VIEW.profiles[0].active,
      ),
    updateConfig: async () => ({
      status: 200,
      body: CONFIG_VIEW.profiles[0].active,
    }),
    listAudit: async () => [{ id: 1, action: "config.update" }],
    listReview: async () => [REVIEW_ITEM],
    getReview: async () => REVIEW_ITEM,
    resolveReview: async () => ({
      status: 200,
      body: { ...REVIEW_ITEM, status: "resolved" },
    }),
    listAppeals: async () => [{ ...REVIEW_ITEM, kind: "appeal" }],
    submitAppeal: async () => ({
      status: 200,
      body: { ...REVIEW_ITEM, kind: "appeal" },
    }),
    submitClaimIntake: async () => ({
      status: 200,
      body: { ...REVIEW_ITEM, kind: "claim_intake" },
    }),
    getMetrics: async () => ({
      benchmark: {
        total: 9,
        verdict_accuracy: 1,
        calibration_error: 0.2,
        by_difficulty: {},
      },
      queue: { open: 1, resolved: 0, by_kind: { evidence_conflict: 1 } },
      claims_count: 1,
    }),
    recordAudit: async () => {},
    listCalibrationRuns: async () => [
      { id: 1, verdict_accuracy: 1, calibration_error: 0.2, total: 9 },
    ],
    recordCalibrationRun: async () => ({
      id: 2,
      verdict_accuracy: 1,
      calibration_error: 0.2,
      total: 9,
    }),
    ...overrides,
  } as unknown as AdminClient;
}

const keys = {
  "admin-key": { scopes: ["admin"] },
  writer: { scopes: ["write"] },
};

describe("gateway admin browse routes", () => {
  it("401 without a key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({ method: "GET", url: "/admin/claims" });
    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("403 when the key lacks the admin scope", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/claims",
      headers: { "x-api-key": "writer" },
    });
    expect(res.statusCode).toBe(403);
    await app.close();
  });

  it("200 lists claims with an admin key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/claims?limit=10",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([RECORD]);
    await app.close();
  });

  it("200 returns a claim's verdict history", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/claims/c1/verdicts",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([RECORD]);
    await app.close();
  });

  it("404 when a claim has no latest verdict", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({ latestVerdict: async () => null }),
    });
    const res = await app.inject({
      method: "GET",
      url: "/admin/claims/nope/verdict",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(404);
    await app.close();
  });

  it("502 when the Trust Engine is unavailable", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({
        listClaims: async () => {
          throw new Error("down");
        },
      }),
    });
    const res = await app.inject({
      method: "GET",
      url: "/admin/claims",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(502);
    await app.close();
  });

  it("403 on config routes without the admin scope", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/config",
      headers: { "x-api-key": "writer" },
    });
    expect(res.statusCode).toBe(403);
    await app.close();
  });

  it("200 returns the config view with an admin key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/config",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual(CONFIG_VIEW);
    await app.close();
  });

  it("forwards a config write and preserves the engine status (200)", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "POST",
      url: "/admin/config",
      headers: { "x-api-key": "admin-key" },
      payload: { profile: "default", actor: "alice" },
    });
    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("passes a 422 validation rejection through unchanged", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({
        updateConfig: async () => ({
          status: 422,
          body: { detail: [{ msg: "must sum to 1.0" }] },
        }),
      }),
    });
    const res = await app.inject({
      method: "POST",
      url: "/admin/config",
      headers: { "x-api-key": "admin-key" },
      payload: { profile: "default", actor: "alice" },
    });
    expect(res.statusCode).toBe(422);
    await app.close();
  });

  it("200 lists audit entries", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/audit",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([{ id: 1, action: "config.update" }]);
    await app.close();
  });

  it("403 on review routes without the admin scope", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/review",
      headers: { "x-api-key": "writer" },
    });
    expect(res.statusCode).toBe(403);
    await app.close();
  });

  it("200 lists the review queue with an admin key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/review?status=open",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual([REVIEW_ITEM]);
    await app.close();
  });

  it("404 when a review item is missing", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({ getReview: async () => null }),
    });
    const res = await app.inject({
      method: "GET",
      url: "/admin/review/999",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(404);
    await app.close();
  });

  it("resolve preserves the engine status (409 already resolved)", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({
        resolveReview: async () => ({
          status: 409,
          body: { detail: "already resolved" },
        }),
      }),
    });
    const res = await app.inject({
      method: "POST",
      url: "/admin/review/1/resolve",
      headers: { "x-api-key": "admin-key" },
      payload: { reviewer: "alice", decision: "dismissed" },
    });
    expect(res.statusCode).toBe(409);
    await app.close();
  });

  it("200 lists appeals with an admin key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/appeals",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()[0].kind).toBe("appeal");
    await app.close();
  });

  it("public appeal submission needs no API key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "POST",
      url: "/v1/appeals",
      payload: { claim_id: "c1", appeal_type: "new_evidence", body: "x" },
    });
    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("public appeal submission preserves a 422 invalid type", async () => {
    const app = buildApp({
      apiKeys: keys,
      admin: fakeAdmin({
        submitAppeal: async () => ({
          status: 422,
          body: { detail: "bad type" },
        }),
      }),
    });
    const res = await app.inject({
      method: "POST",
      url: "/v1/appeals",
      payload: { claim_id: "c1", appeal_type: "nope", body: "x" },
    });
    expect(res.statusCode).toBe(422);
    await app.close();
  });

  it("public claim submission needs no API key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "POST",
      url: "/v1/claims/submit",
      payload: { text: "Country Z shelled a hospital." },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().kind).toBe("claim_intake");
    await app.close();
  });

  it("403 on metrics without the admin scope", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/metrics",
      headers: { "x-api-key": "writer" },
    });
    expect(res.statusCode).toBe(403);
    await app.close();
  });

  it("200 returns metrics with an admin key", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const res = await app.inject({
      method: "GET",
      url: "/admin/metrics",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().benchmark.verdict_accuracy).toBe(1);
    expect(res.json().queue.open).toBe(1);
    await app.close();
  });

  it("lists calibration runs and records a new one (admin only)", async () => {
    const app = buildApp({ apiKeys: keys, admin: fakeAdmin() });
    const denied = await app.inject({
      method: "GET",
      url: "/admin/calibration",
    });
    expect(denied.statusCode).toBe(401);

    const list = await app.inject({
      method: "GET",
      url: "/admin/calibration",
      headers: { "x-api-key": "admin-key" },
    });
    expect(list.statusCode).toBe(200);
    expect(list.json()[0].verdict_accuracy).toBe(1);

    const run = await app.inject({
      method: "POST",
      url: "/admin/calibration/run",
      headers: { "x-api-key": "admin-key" },
    });
    expect(run.statusCode).toBe(200);
    expect(run.json().id).toBe(2);
    await app.close();
  });
});
