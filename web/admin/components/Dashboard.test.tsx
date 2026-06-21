import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

const RUN = {
  id: 1,
  recorded_time: "2024-12-01T00:00:00Z",
  total: 9,
  verdict_accuracy: 1.0,
  calibration_error: 0.206,
  payload: {},
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** URL-aware fetch mock: dashboard calls /admin/metrics and /admin/calibration. */
function mockGateway(
  opts: {
    metrics?: unknown;
    metricsStatus?: number;
    runs?: unknown[];
  } = {},
) {
  return vi
    .spyOn(globalThis, "fetch")
    .mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/admin/metrics")) {
        return json(opts.metrics ?? METRICS, opts.metricsStatus ?? 200);
      }
      if (url.includes("/admin/calibration/run")) {
        return json({ ...RUN, id: 2 });
      }
      if (url.includes("/admin/calibration")) {
        return json(opts.runs ?? [RUN]);
      }
      return json({}, 404);
    });
}

afterEach(() => vi.restoreAllMocks());

describe("Dashboard", () => {
  it("renders benchmark accuracy, calibration, and queue health", async () => {
    mockGateway();
    render(<Dashboard apiKey="admin-key" />);
    expect(await screen.findByText("100.0%")).toBeTruthy();
    expect(screen.getAllByText("0.206").length).toBeGreaterThan(0);
    expect(screen.getByText(/evidence_conflict: 2/)).toBeTruthy();
    expect(screen.getByText(/Claims with verdicts: 3/)).toBeTruthy();
  });

  it("lists calibration runs and records a new one", async () => {
    mockGateway({ runs: [RUN] });
    render(<Dashboard apiKey="admin-key" />);
    expect(await screen.findByText(/#1 @/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Record a run" }));
    await waitFor(() =>
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.some(([u]) =>
          String(u).includes("/admin/calibration/run"),
        ),
      ).toBe(true),
    );
  });

  it("tolerates a missing benchmark", async () => {
    mockGateway({ metrics: { ...METRICS, benchmark: null } });
    render(<Dashboard apiKey="admin-key" />);
    expect(await screen.findByText(/Benchmark unavailable/)).toBeTruthy();
  });

  it("signals an auth error on 403", async () => {
    mockGateway({ metricsStatus: 403 });
    const onAuthError = vi.fn();
    render(<Dashboard apiKey="bad" onAuthError={onAuthError} />);
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(onAuthError).toHaveBeenCalled();
  });
});
