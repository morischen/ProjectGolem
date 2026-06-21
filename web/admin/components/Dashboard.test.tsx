import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Dashboard } from "./Dashboard";

const METRICS = {
  benchmark: {
    total: 9,
    verdict_accuracy: 1.0,
    calibration_error: 0.206,
    by_difficulty: { hard: 1.0, tractable: 1.0 },
  },
  queue: { open: 2, resolved: 1, by_kind: { evidence_conflict: 2, appeal: 1 } },
  claims_count: 3,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("Dashboard", () => {
  it("renders benchmark accuracy, calibration, and queue health", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json(METRICS));
    render(<Dashboard apiKey="admin-key" />);

    expect(await screen.findByText("100.0%")).toBeTruthy(); // accuracy
    expect(screen.getByText("0.206")).toBeTruthy(); // ECE
    expect(screen.getByText(/evidence_conflict: 2/)).toBeTruthy();
    expect(screen.getByText(/Claims with verdicts: 3/)).toBeTruthy();
  });

  it("tolerates a missing benchmark", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      json({ ...METRICS, benchmark: null }),
    );
    render(<Dashboard apiKey="admin-key" />);
    expect(await screen.findByText(/Benchmark unavailable/)).toBeTruthy();
  });

  it("signals an auth error on 403", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({}, 403));
    const onAuthError = vi.fn();
    render(<Dashboard apiKey="bad" onAuthError={onAuthError} />);
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(onAuthError).toHaveBeenCalled();
  });
});
