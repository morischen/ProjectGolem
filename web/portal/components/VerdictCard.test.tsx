import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { sampleEvidence, sampleResult } from "../lib/sample";
import { VerdictCard } from "./VerdictCard";

describe("VerdictCard", () => {
  it("shows the verdict and confidence", () => {
    render(<VerdictCard result={sampleResult} evidence={sampleEvidence} />);
    expect(
      screen.getByRole("heading", { name: sampleResult.verdict }),
    ).toBeTruthy();
    expect(screen.getByText(/Confidence 78%/)).toBeTruthy();
  });

  it("surfaces the strongest opposing evidence", () => {
    render(<VerdictCard result={sampleResult} evidence={sampleEvidence} />);
    // The single contradicting source must be shown, not buried.
    expect(screen.getByText(/ngo-report-1/)).toBeTruthy();
  });

  it("renders all six breakdown components", () => {
    render(<VerdictCard result={sampleResult} evidence={sampleEvidence} />);
    for (const label of [
      "Source reliability",
      "Corroboration",
      "Evidence quality",
      "Independence",
      "Freshness",
      "Weighted total",
    ]) {
      expect(screen.getByText(new RegExp(label))).toBeTruthy();
    }
  });
});
