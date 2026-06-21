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
});
