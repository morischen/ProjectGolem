import { afterEach, describe, expect, it, vi } from "vitest";
import { buildApp } from "../src/app";

const EVIDENCE = [
  {
    id: "e1",
    source_id: "s1",
    source_tier: 1,
    relation: "supports",
    quality: 1,
    freshness: 1,
  },
];

function mockScoreFetch() {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ verdict: "Verified" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  );
}

afterEach(() => vi.restoreAllMocks());

describe("gateway API-key auth", () => {
  const keys = {
    "good-key": { scopes: ["write"] },
    reader: { scopes: ["read"] },
  };

  it("401 when a protected route is called without a key", async () => {
    const app = buildApp({ apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload: { evidence: EVIDENCE },
    });
    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("403 when the key lacks the required scope", async () => {
    const app = buildApp({ apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      headers: { "x-api-key": "reader" },
      payload: { evidence: EVIDENCE },
    });
    expect(res.statusCode).toBe(403);
    await app.close();
  });

  it("200 with a valid key carrying the scope", async () => {
    mockScoreFetch();
    const app = buildApp({ apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      headers: { "x-api-key": "good-key" },
      payload: { evidence: EVIDENCE },
    });
    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("auth disabled (no keys) allows the request", async () => {
    mockScoreFetch();
    const app = buildApp({ apiKeys: {} });
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload: { evidence: EVIDENCE },
    });
    expect(res.statusCode).toBe(200);
    await app.close();
  });

  it("health stays public", async () => {
    const app = buildApp({ apiKeys: keys });
    const res = await app.inject({ method: "GET", url: "/health" });
    expect(res.statusCode).toBe(200);
    await app.close();
  });
});
