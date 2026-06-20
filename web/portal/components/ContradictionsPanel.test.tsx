import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { sampleEvidence } from "../lib/sample";
import { ContradictionsPanel } from "./ContradictionsPanel";

describe("ContradictionsPanel", () => {
  it("lists contradicting evidence with a count", () => {
    render(<ContradictionsPanel evidence={sampleEvidence} />);
    expect(
      screen.getByRole("region", { name: "contradicting evidence" }),
    ).toBeTruthy();
    expect(screen.getByText(/Contradicting evidence \(1\)/)).toBeTruthy();
    expect(screen.getByText(/ngo-report-1/)).toBeTruthy();
  });

  it("shows an explicit empty state when there is none", () => {
    const onlySupporting = sampleEvidence.filter(
      (e) => e.relation !== "contradicts",
    );
    render(<ContradictionsPanel evidence={onlySupporting} />);
    expect(
      screen.getByText(/No contradicting evidence on record/),
    ).toBeTruthy();
  });
});
