import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AccessManagement } from "./AccessManagement";
import type { KeyMeta } from "../lib/adminApi";

const KEY: KeyMeta = {
  id: "k1",
  label: "ci",
  scopes: ["read"],
  prefix: "abc123…",
  createdAt: "2024-01-01T00:00:00Z",
  disabled: false,
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("AccessManagement", () => {
  it("lists keys by prefix (no secret)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json([KEY]));
    render(<AccessManagement apiKey="admin-key" />);
    expect(await screen.findByText("abc123…")).toBeTruthy();
    expect(screen.getByText("ci")).toBeTruthy();
  });

  it("creates a key and shows the secret once", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json([])) // initial list
      .mockResolvedValueOnce(
        json({ key: "eip_supersecret", meta: { ...KEY, id: "k2" } }, 201),
      ) // create
      .mockResolvedValueOnce(json([{ ...KEY, id: "k2" }])); // reload

    render(<AccessManagement apiKey="admin-key" />);
    await screen.findByRole("form", { name: "create key" });

    fireEvent.change(screen.getByLabelText("key label"), {
      target: { value: "deploy" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create key" }));

    expect(await screen.findByText("eip_supersecret")).toBeTruthy();
    const postCall = fetchSpy.mock.calls.find(
      ([, init]) => init?.method === "POST",
    );
    const body = JSON.parse(String(postCall?.[1]?.body));
    expect(body.label).toBe("deploy");
    expect(body.scopes).toContain("read");
  });

  it("revokes a key", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json([KEY])) // list
      .mockResolvedValueOnce(json({ ...KEY, disabled: true })) // disable
      .mockResolvedValueOnce(json([{ ...KEY, disabled: true }])); // reload

    render(<AccessManagement apiKey="admin-key" />);
    fireEvent.click(await screen.findByRole("button", { name: "Revoke" }));

    await waitFor(() => expect(screen.getByText("disabled")).toBeTruthy());
    const disableCall = fetchSpy.mock.calls.find(([url]) =>
      String(url).includes("/disable"),
    );
    expect(disableCall).toBeTruthy();
  });
});
