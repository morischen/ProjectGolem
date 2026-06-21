import { afterEach, describe, expect, it, vi } from "vitest";
import {
  AdminApiError,
  getConfig,
  updateConfig,
  type ConfigUpdateBody,
} from "./adminApi";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const BODY: ConfigUpdateBody = {
  profile: "default",
  actor: "alice",
  source_reliability: 0.3,
  corroboration: 0.25,
  evidence_quality: 0.2,
  independence: 0.15,
  freshness: 0.1,
  tier_reliability: { "1": 1.0 },
  strength_floor: 0.3,
  mixed_conflict_threshold: 0.35,
  verified_threshold: 0.8,
};

afterEach(() => vi.restoreAllMocks());

describe("config API client", () => {
  it("getConfig sends the API key", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(json({ profiles: [] }));
    await getConfig("admin-key");
    expect(String(spy.mock.calls[0][0])).toContain("/admin/config");
    expect(
      (spy.mock.calls[0][1]?.headers as Record<string, string>)["x-api-key"],
    ).toBe("admin-key");
  });

  it("updateConfig POSTs the body and returns the new record", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(json({ profile: "default", version: 2 }));
    const rec = await updateConfig("admin-key", BODY);
    expect(rec.version).toBe(2);
    expect(spy.mock.calls[0][1]?.method).toBe("POST");
  });

  it("updateConfig throws AdminApiError carrying the 422 detail", async () => {
    // Fresh Response per call — a Response body can only be read once.
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ detail: [{ msg: "must sum to 1.0" }] }, 422),
    );
    const err = await updateConfig("admin-key", BODY).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(AdminApiError);
    expect((err as AdminApiError).status).toBe(422);
    expect((err as AdminApiError).detail).toEqual([{ msg: "must sum to 1.0" }]);
  });
});
