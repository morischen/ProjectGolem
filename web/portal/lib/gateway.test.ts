import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchVerdict } from "./gateway";
import { sampleResult } from "./sample";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("fetchVerdict", () => {
  it("returns live data when the gateway responds", async () => {
    const live = { ...sampleResult, verdict: "Verified" as const, score: 0.9 };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(live), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const view = await fetchVerdict();
    expect(view.live).toBe(true);
    expect(view.result.verdict).toBe("Verified");
  });

  it("falls back to sample data when the gateway is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new Error("connection refused"),
    );

    const view = await fetchVerdict();
    expect(view.live).toBe(false);
    expect(view.result).toEqual(sampleResult);
  });

  it("falls back on a non-2xx response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );

    const view = await fetchVerdict();
    expect(view.live).toBe(false);
  });
});
