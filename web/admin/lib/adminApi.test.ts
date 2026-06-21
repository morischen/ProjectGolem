import { afterEach, describe, expect, it, vi } from "vitest";
import {
  AdminApiError,
  claimHistory,
  listClaims,
  type VerdictRecord,
} from "./adminApi";

const RECORD: VerdictRecord = {
  claim_id: "c1",
  version: 1,
  verdict: "Verified",
  score: 0.9,
  weights_version: "v0",
  knowledge_time: "2024-12-01T00:00:00Z",
  event_time: null,
  payload: {},
};

function mockFetch(body: unknown, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
}

afterEach(() => vi.restoreAllMocks());

describe("adminApi", () => {
  it("sends the API key and returns the claims list", async () => {
    const spy = mockFetch([RECORD]);
    const rows = await listClaims("admin-key", { limit: 10 });
    expect(rows).toEqual([RECORD]);
    const [url, init] = spy.mock.calls[0];
    expect(String(url)).toContain("/admin/claims?limit=10");
    expect((init?.headers as Record<string, string>)["x-api-key"]).toBe(
      "admin-key",
    );
  });

  it("fetches a claim's history", async () => {
    const spy = mockFetch([RECORD]);
    const rows = await claimHistory("admin-key", "c 1");
    expect(rows).toEqual([RECORD]);
    expect(String(spy.mock.calls[0][0])).toContain(
      "/admin/claims/c%201/verdicts",
    );
  });

  it("throws AdminApiError with the status on a non-2xx response", async () => {
    mockFetch({ error: "nope" }, 403);
    await expect(listClaims("bad")).rejects.toMatchObject({
      name: "AdminApiError",
      status: 403,
    });
    await expect(listClaims("bad")).rejects.toBeInstanceOf(AdminApiError);
  });
});
