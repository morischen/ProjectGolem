import { describe, expect, it, vi } from "vitest";
import { buildApp } from "../src/app";
import type { ClaimClient } from "../src/claimClient";
import type { EvidenceClient } from "../src/evidenceClient";
import type { ScorerClient } from "../src/scorerClient";

const CLAIM = {
  id: "c1",
  text: "Country X attacked City Y on 2024-01-02.",
  claim_type: "empirical",
};

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

const RESULT = { verdict: "Verified", score: 0.9 };

function clients(
  overrides: {
    claim?: Partial<ClaimClient>;
    evidence?: Partial<EvidenceClient>;
    scorer?: Partial<ScorerClient>;
  } = {},
) {
  const extract = vi.fn(async () => CLAIM);
  const gather = vi.fn(async () => EVIDENCE);
  const score = vi.fn(async () => RESULT);
  return {
    claim: { extract, ...overrides.claim } as unknown as ClaimClient,
    evidence: { gather, ...overrides.evidence } as unknown as EvidenceClient,
    scorer: { score, ...overrides.scorer } as unknown as ScorerClient,
    spies: { extract, gather, score },
  };
}

const keys = { writer: { scopes: ["write"] } };

describe("gateway /v1/assess (end-to-end orchestration)", () => {
  it("400 when text or claim_id is missing", async () => {
    const c = clients();
    const app = buildApp({ ...c, apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/assess",
      headers: { "x-api-key": "writer" },
      payload: { text: "only text" },
    });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("401 without a write key", async () => {
    const c = clients();
    const app = buildApp({ ...c, apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/assess",
      payload: { text: "x", claim_id: "c1" },
    });
    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("runs extract -> gather -> score and returns the assembled result", async () => {
    const c = clients();
    const app = buildApp({ ...c, apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/assess",
      headers: { "x-api-key": "writer" },
      payload: {
        text: "Country X attacked City Y.",
        claim_id: "c1",
        candidates: [{ id: "x" }],
      },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.claim.id).toBe("c1");
    expect(body.evidence).toEqual(EVIDENCE);
    expect(body.result.verdict).toBe("Verified");

    // Pipeline wiring: extracted claim text feeds gather; evidence + claim_id feed score.
    expect(c.spies.extract).toHaveBeenCalledWith({
      text: "Country X attacked City Y.",
      claimId: "c1",
    });
    expect(c.spies.gather).toHaveBeenCalledWith({
      claimText: CLAIM.text,
      candidates: [{ id: "x" }],
    });
    expect(c.spies.score).toHaveBeenCalledWith(
      expect.objectContaining({ evidence: EVIDENCE, claimId: "c1" }),
    );
    await app.close();
  });

  it("502 when an engine in the pipeline fails", async () => {
    const c = clients({
      evidence: {
        gather: vi.fn(async () => {
          throw new Error("evidence down");
        }),
      },
    });
    const app = buildApp({ ...c, apiKeys: keys });
    const res = await app.inject({
      method: "POST",
      url: "/v1/assess",
      headers: { "x-api-key": "writer" },
      payload: { text: "x", claim_id: "c1" },
    });
    expect(res.statusCode).toBe(502);
    await app.close();
  });
});
