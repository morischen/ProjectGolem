import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ClaimSubmit } from "./ClaimSubmit";

afterEach(() => vi.restoreAllMocks());

describe("ClaimSubmit", () => {
  it("exposes an accessible propose affordance and states triage", () => {
    render(<ClaimSubmit />);
    expect(screen.getByRole("region", { name: "submit a claim" })).toBeTruthy();
    expect(screen.getByText(/triaged by reviewers/)).toBeTruthy();
  });

  it("opens the form and submits a claim to the gateway", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: 1, kind: "claim_intake" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    const onSubmitted = vi.fn();
    render(<ClaimSubmit onSubmitted={onSubmitted} />);

    fireEvent.click(screen.getByRole("button", { name: "Propose a claim" }));
    fireEvent.change(screen.getByLabelText("claim text"), {
      target: { value: "Country Z shelled a hospital on 2024-03-01." },
    });
    fireEvent.submit(screen.getByRole("form", { name: "claim form" }));

    expect(await screen.findByRole("status")).toBeTruthy();
    await waitFor(() => expect(onSubmitted).toHaveBeenCalledOnce());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/v1/claims/submit");
    expect(JSON.parse(String(init?.body)).text).toContain("Country Z");
  });

  it("shows an error when submission fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );
    render(<ClaimSubmit />);
    fireEvent.click(screen.getByRole("button", { name: "Propose a claim" }));
    fireEvent.change(screen.getByLabelText("claim text"), {
      target: { value: "x" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "claim form" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
