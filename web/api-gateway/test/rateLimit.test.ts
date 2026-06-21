import { afterEach, describe, expect, it, vi } from "vitest";
import { buildApp } from "../src/app";
import { createRateLimiter, InMemoryRateLimitStore } from "../src/rateLimit";

afterEach(() => vi.restoreAllMocks());

describe("createRateLimiter", () => {
  it("allows up to the limit, then blocks, then resets after the window", () => {
    let t = 1000;
    const check = createRateLimiter({ limit: 2, windowMs: 100, now: () => t });

    expect(check("k").allowed).toBe(true); // 1
    expect(check("k").allowed).toBe(true); // 2
    expect(check("k").allowed).toBe(false); // 3 -> blocked

    t += 100; // advance past the window
    expect(check("k").allowed).toBe(true); // resets
  });

  it("keys are independent", () => {
    const check = createRateLimiter({ limit: 1, windowMs: 1000, now: () => 0 });
    expect(check("a").allowed).toBe(true);
    expect(check("b").allowed).toBe(true);
    expect(check("a").allowed).toBe(false);
  });

  it("a shared store enforces the limit across limiter instances (distributed)", () => {
    // Two limiters = two gateway replicas sharing one counter backend.
    const store = new InMemoryRateLimitStore();
    const a = createRateLimiter({
      limit: 2,
      windowMs: 1000,
      now: () => 0,
      store,
    });
    const b = createRateLimiter({
      limit: 2,
      windowMs: 1000,
      now: () => 0,
      store,
    });
    expect(a("k").allowed).toBe(true); // replica A, hit 1
    expect(b("k").allowed).toBe(true); // replica B, hit 2 (shared)
    expect(a("k").allowed).toBe(false); // hit 3 -> blocked across both
  });
});

describe("gateway rate limiting", () => {
  it("returns 429 once the limit is exceeded", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ verdict: "Verified" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    const app = buildApp({
      apiKeys: {}, // auth disabled; isolate rate-limit behavior
      rateLimit: { limit: 1, windowMs: 60_000, now: () => 0 },
    });
    const payload = {
      evidence: [
        {
          id: "e1",
          source_id: "s1",
          source_tier: 1,
          relation: "supports",
          quality: 1,
          freshness: 1,
        },
      ],
    };

    const first = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload,
    });
    expect(first.statusCode).toBe(200);
    expect(first.headers["x-ratelimit-remaining"]).toBe("0");

    const second = await app.inject({
      method: "POST",
      url: "/v1/score",
      payload,
    });
    expect(second.statusCode).toBe(429);
    await app.close();
  });
});
