import { afterEach, describe, expect, it, vi } from "vitest";
import type { Evidence } from "@eip/contracts";
import { buildApp } from "../src/app";

const FAKE_EVIDENCE: Evidence[] = [
  {
    id: "c1",
    source_id: "s1",
    source_tier: 1,
    relation: "supports",
    quality: 0.9,
    freshness: 0.8,
  },
];

const CANDIDATE = {
  id: "c1",
  source_id: "s1",
  source_tier: 1,
  content: "source text",
  quality: 0.9,
  freshness: 0.8,
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("gateway POST /v1/gather", () => {
  it("proxies to the evidence-engine and returns Evidence[]", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(FAKE_EVIDENCE), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/gather",
      payload: { claim_text: "a claim", candidates: [CANDIDATE] },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json()[0].relation).toBe("supports");
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8002/v1/gather",
      expect.objectContaining({ method: "POST" }),
    );
    await app.close();
  });

  it("rejects a body without claim_text/candidates (400)", async () => {
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/gather",
      payload: { claim_text: "no candidates" },
    });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 502 when the evidence-engine errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/gather",
      payload: { claim_text: "a claim", candidates: [CANDIDATE] },
    });
    expect(res.statusCode).toBe(502);
    await app.close();
  });
});
