import type { Claim } from "@eip/contracts";

export interface ExtractInput {
  text: string;
  claimId: string;
}

/**
 * Typed client for the Claim Engine's HTTP surface (POST /v1/extract).
 * Returns the generated `Claim` contract. The gateway proxies extraction here;
 * it does not run the LLM or score.
 */
export class ClaimClient {
  constructor(private readonly baseUrl: string) {}

  async extract(input: ExtractInput): Promise<Claim> {
    const res = await fetch(`${this.baseUrl}/v1/extract`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: input.text, claim_id: input.claimId }),
    });
    if (!res.ok) {
      throw new Error(`claim-engine responded ${res.status}`);
    }
    return (await res.json()) as Claim;
  }
}
