import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssessClaim } from "./AssessClaim";

const RESULT = {
  claim: { id: "c1", text: "Country X attacked City Y." },
  evidence: [{ id: "e1", source_id: "s1", relation: "supports" }],
  result: {
    verdict: "Verified",
    score: 0.91,
    weights_version: "default.v1",
    breakdown: { source_reliability: 1.0, corroboration: 0.5 },
  },
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

async function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("claim id"), {
    target: { value: "c1" },
  });
  fireEvent.change(screen.getByLabelText("claim text"), {
    target: { value: "Country X attacked City Y." },
  });
  fireEvent.submit(screen.getByRole("form", { name: "assess form" }));
}

describe("AssessClaim", () => {
  it("submits the pipeline request and renders the verdict + evidence", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(json(RESULT));
    render(<AssessClaim apiKey="write-key" />);
    await fillAndSubmit();

    expect(await screen.findByText(/Verdict: Verified/)).toBeTruthy();
    expect(screen.getByText(/s1 — supports/)).toBeTruthy();
    expect(screen.getByText(/config: default.v1/)).toBeTruthy();

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/v1/assess");
    const body = JSON.parse(String(init?.body));
    expect(body.claim_id).toBe("c1");
    expect(body.candidates).toEqual([]);
  });

  it("rejects invalid candidates JSON before calling the gateway", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(json(RESULT));
    render(<AssessClaim apiKey="write-key" />);
    fireEvent.change(screen.getByLabelText("candidates json"), {
      target: { value: "{ not an array" },
    });
    await fillAndSubmit();
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("signals an auth error on 403", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ error: "no" }, 403));
    const onAuthError = vi.fn();
    render(<AssessClaim apiKey="bad" onAuthError={onAuthError} />);
    await fillAndSubmit();
    await waitFor(() => expect(onAuthError).toHaveBeenCalled());
    expect(screen.getByRole("alert").textContent).toMatch(/write-scoped/);
  });
});
