import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppealEntry } from "./AppealEntry";

describe("AppealEntry", () => {
  it("exposes an accessible appeal affordance and states appeals are public", () => {
    render(<AppealEntry />);
    expect(screen.getByRole("region", { name: "appeal" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Submit an appeal" }),
    ).toBeTruthy();
    expect(screen.getByText(/logged publicly/)).toBeTruthy();
  });

  it("invokes the handler when the appeal button is clicked", () => {
    const onAppeal = vi.fn();
    render(<AppealEntry onAppeal={onAppeal} />);
    screen.getByRole("button", { name: "Submit an appeal" }).click();
    expect(onAppeal).toHaveBeenCalledOnce();
  });
});
