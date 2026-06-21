import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ClaimsBrowser } from "./ClaimsBrowser";
import type { VerdictRecord } from "../lib/adminApi";

const CLAIM: VerdictRecord = {
  claim_id: "c1",
  version: 2,
  verdict: "Verified",
  score: 0.92,
  weights_version: "v0",
  knowledge_time: "2024-12-01T00:00:00Z",
  event_time: null,
  payload: {},
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("ClaimsBrowser", () => {
  it("lists claims and drills into a claim's history", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse([CLAIM])) // listClaims
      .mockResolvedValueOnce(
        jsonResponse([
          { ...CLAIM, version: 1, verdict: "Mixed Evidence" },
          CLAIM,
        ]),
      ); // claimHistory

    render(<ClaimsBrowser apiKey="admin-key" />);

    const claimButton = await screen.findByRole("button", { name: "c1" });
    expect(screen.getByText("Verified")).toBeTruthy();

    fireEvent.click(claimButton);
    await screen.findByRole("region", { name: "history for c1" });
    expect(await screen.findByText(/v1: Mixed Evidence/)).toBeTruthy();
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("renders an empty state when there are no verdicts", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
    render(<ClaimsBrowser apiKey="admin-key" />);
    expect(await screen.findByText(/No verdicts recorded yet/)).toBeTruthy();
  });

  it("signals an auth error and shows a denial message on 403", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: "denied" }, 403),
    );
    const onAuthError = vi.fn();
    render(<ClaimsBrowser apiKey="bad-key" onAuthError={onAuthError} />);
    expect(await screen.findByRole("alert")).toBeTruthy();
    await waitFor(() => expect(onAuthError).toHaveBeenCalled());
  });
});
