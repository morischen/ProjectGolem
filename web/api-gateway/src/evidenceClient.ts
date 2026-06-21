import type { Evidence } from "@eip/contracts";

export interface GatherInput {
  claimText: string;
  candidates: unknown[];
}

export interface IndependenceInput {
  sourceIds: string[];
  citations: [string, string][];
}

export interface IndependenceResult {
  distinct_sources: number;
  independent_groups: number;
  independence_ratio: number;
  groups: string[][];
}

/**
 * Typed client for the Evidence Engine's HTTP surface (POST /v1/gather).
 * Returns the generated `Evidence[]` contract. Candidates are opaque to the
 * gateway — it forwards them; classification happens in the Python service.
 */
export class EvidenceClient {
  constructor(private readonly baseUrl: string) {}

  async gather(input: GatherInput): Promise<Evidence[]> {
    const res = await fetch(`${this.baseUrl}/v1/gather`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        claim_text: input.claimText,
        candidates: input.candidates,
      }),
    });
    if (!res.ok) {
      throw new Error(`evidence-engine responded ${res.status}`);
    }
    return (await res.json()) as Evidence[];
  }

  /** Provenance analysis (ADR-0007): graph-derived independence_ratio over sources. */
  async independence(input: IndependenceInput): Promise<IndependenceResult> {
    const res = await fetch(`${this.baseUrl}/v1/independence`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        source_ids: input.sourceIds,
        citations: input.citations,
      }),
    });
    if (!res.ok) {
      throw new Error(`evidence-engine responded ${res.status}`);
    }
    return (await res.json()) as IndependenceResult;
  }
}
