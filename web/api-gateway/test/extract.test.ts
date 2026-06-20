import { afterEach, describe, expect, it, vi } from "vitest";
import type { Claim } from "@eip/contracts";
import { buildApp } from "../src/app";

const FAKE_CLAIM: Claim = {
  id: "c1",
  text: "Country X attacked City Y.",
  claim_type: "empirical",
  actors: ["Country X"],
  targets: ["City Y"],
  events: [],
  locations: [],
  dates: [],
  assertions: [],
  language: null,
  source_url: null,
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("gateway POST /v1/extract", () => {
  it("proxies to the claim-engine and returns its Claim", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(FAKE_CLAIM), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/extract",
      payload: { text: "X attacked Y", claim_id: "c1" },
    });

    expect(res.statusCode).toBe(200);
    expect(res.json().claim_type).toBe("empirical");
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8001/v1/extract",
      expect.objectContaining({ method: "POST" }),
    );
    await app.close();
  });

  it("rejects a body without text/claim_id (400)", async () => {
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/extract",
      payload: { text: "missing claim_id" },
    });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("returns 502 when the claim-engine errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );
    const app = buildApp();
    const res = await app.inject({
      method: "POST",
      url: "/v1/extract",
      payload: { text: "x", claim_id: "c2" },
    });
    expect(res.statusCode).toBe(502);
    await app.close();
  });
});
