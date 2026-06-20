import { afterEach, describe, expect, it, vi } from "vitest";
import type { Evidence, TrustResult } from "@eip/contracts";
import { buildApp } from "../src/app";

const EVIDENCE: Evidence[] = [
  {
    id: "e1",
    source_id: "s1",
    source_tier: 1,
    relation: "supports",
    quality: 1,
    freshness: 1,
  },
];

const FAKE_RESULT: TrustResult = {
  score: 0.92,
  verdict: "Verified",
  breakdown: {
    source_reliability: 1,
    corroboration: 0.875,
    evidence_quality: 1,
    independence: 0.667,
    freshness: 1,
    weighted_total: 0.92,
  },
  weights_version: "2026-06-19.v0",
  relevant_count: 1,
  supporting_count: 1,
  contradicting_count: 0,
  net_support: 1,
  conflict_ratio: 0,
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("gateway POST /v1/score", () => {
  it("proxies to the trust-engine and returns its TrustResult", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(FAKE_RESULT), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload: { evidence: EVIDENCE },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().verdict).toBe("Verified");
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8000/v1/score",
      expect.objectContaining({ method: "POST" }),
    );
    await app.close();
  });

  it("rejects a body without evidence[] (400)", async () => {
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload: {},
    });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 502 when the trust-engine errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload: { evidence: EVIDENCE },
    });
    expect(res.statusCode).toBe(502);
    await app.close();
  });
});
