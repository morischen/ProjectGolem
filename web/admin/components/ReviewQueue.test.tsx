import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReviewQueue } from "./ReviewQueue";
import type { ReviewRecord } from "../lib/adminApi";

const ITEM: ReviewRecord = {
  id: 1,
  claim_id: "c1",
  kind: "evidence_conflict",
  status: "open",
  created_time: "2024-01-01T00:00:00Z",
  detail: { score: 0.5 },
  resolution: null,
  resolved_time: null,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("ReviewQueue", () => {
  it("lists open review items", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json([ITEM]));
    render(<ReviewQueue apiKey="admin-key" mode="review" />);
    expect(await screen.findByText("evidence_conflict")).toBeTruthy();
  });

  it("shows an empty state when nothing is queued", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json([]));
    render(<ReviewQueue apiKey="admin-key" mode="review" />);
    expect(await screen.findByText(/Nothing to review/)).toBeTruthy();
  });

  it("resolves an item with an override and reloads", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json([ITEM])) // initial list
      .mockResolvedValueOnce(json({ ...ITEM, status: "resolved" })) // resolve POST
      .mockResolvedValueOnce(json([])); // reload list

    render(<ReviewQueue apiKey="admin-key" mode="review" />);
    fireEvent.click(await screen.findByRole("button", { name: "Resolve" }));

    await screen.findByRole("form", { name: "resolve form" });
    fireEvent.change(screen.getByLabelText("reviewer"), {
      target: { value: "alice" },
    });
    fireEvent.change(screen.getByLabelText("decision"), {
      target: { value: "override" },
    });
    // Override verdict selector appears.
    fireEvent.change(screen.getByLabelText("override verdict"), {
      target: { value: "False" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "resolve form" }));

    await waitFor(() =>
      expect(screen.getByText(/Nothing to review/)).toBeTruthy(),
    );
    const postCall = fetchSpy.mock.calls.find(
      ([, init]) => init?.method === "POST",
    );
    const body = JSON.parse(String(postCall?.[1]?.body));
    expect(body.decision).toBe("override");
    expect(body.override_verdict).toBe("False");
    expect(body.reviewer).toBe("alice");
  });

  it("appeals mode lists appeals", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      json([{ ...ITEM, kind: "appeal" }]),
    );
    render(<ReviewQueue apiKey="admin-key" mode="appeals" />);
    expect(await screen.findByText("appeal")).toBeTruthy();
    expect(
      String(
        (vi.mocked(globalThis.fetch).mock.calls[0][0] as unknown as string) ??
          "",
      ),
    ).toContain("/admin/appeals");
  });
});
