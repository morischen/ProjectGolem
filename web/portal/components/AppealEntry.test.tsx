import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppealEntry } from "./AppealEntry";

afterEach(() => vi.restoreAllMocks());

describe("AppealEntry", () => {
  it("exposes an accessible appeal affordance and states appeals are public", () => {
    render(<AppealEntry />);
    expect(screen.getByRole("region", { name: "appeal" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Submit an appeal" }),
    ).toBeTruthy();
    expect(screen.getByText(/logged publicly/)).toBeTruthy();
  });

  it("opens the form and submits an appeal to the gateway", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: 1, kind: "appeal" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    const onAppeal = vi.fn();
    render(<AppealEntry claimId="c1" onAppeal={onAppeal} />);

    fireEvent.click(screen.getByRole("button", { name: "Submit an appeal" }));
    fireEvent.change(screen.getByLabelText("appeal details"), {
      target: { value: "a newly declassified document" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "appeal form" }));

    expect(await screen.findByRole("status")).toBeTruthy();
    await waitFor(() => expect(onAppeal).toHaveBeenCalledOnce());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/v1/appeals");
    const sent = JSON.parse(String(init?.body));
    expect(sent.claim_id).toBe("c1");
    expect(sent.appeal_type).toBe("new_evidence");
  });

  it("shows an error when submission fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 }),
    );
    render(<AppealEntry claimId="c1" />);
    fireEvent.click(screen.getByRole("button", { name: "Submit an appeal" }));
    fireEvent.change(screen.getByLabelText("appeal details"), {
      target: { value: "x" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "appeal form" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
