import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app";

describe("api-gateway", () => {
  it("GET /health returns ok", async () => {
    const app = buildApp();
    const res = await app.inject({ method: "GET", url: "/health" });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual({ status: "ok" });
    await app.close();
  });

  it("GET /v1/info lists the six verdicts and disclaims scoring", async () => {
    const app = buildApp();
    const res = await app.inject({ method: "GET", url: "/v1/info" });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.verdicts).toHaveLength(6);
    expect(body.role).toContain("no scoring");
    await app.close();
  });
});
