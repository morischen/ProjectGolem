import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConfigEditor } from "./ConfigEditor";
import type { ConfigRecord, ConfigView } from "../lib/adminApi";

const WEIGHTS = {
  version: "default.v1",
  source_reliability: 0.3,
  corroboration: 0.25,
  evidence_quality: 0.2,
  independence: 0.15,
  freshness: 0.1,
  tier_reliability: { "1": 1.0, "2": 0.8, "3": 0.6, "4": 0.35 },
  strength_floor: 0.3,
  mixed_conflict_threshold: 0.35,
  verified_threshold: 0.8,
};

const ACTIVE: ConfigRecord = {
  profile: "default",
  version: 1,
  payload: WEIGHTS,
  knowledge_time: "2024-01-01T00:00:00Z",
  actor: "system",
  note: "seed",
};

const VIEW: ConfigView = {
  profiles: [{ profile: "default", active: ACTIVE, versions: [1] }],
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("ConfigEditor", () => {
  it("loads and shows the active config + weights", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(VIEW)) // getConfig
      .mockResolvedValueOnce(json([ACTIVE])); // configHistory

    render(<ConfigEditor apiKey="admin-key" />);
    await screen.findByRole("form", { name: "config editor" });
    expect((screen.getByLabelText("freshness") as HTMLInputElement).value).toBe(
      "0.1",
    );
    expect(screen.getByText(/Sum: 1.00/)).toBeTruthy();
  });

  it("disables save when component weights do not sum to 1.0", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(VIEW))
      .mockResolvedValueOnce(json([ACTIVE]));

    render(<ConfigEditor apiKey="admin-key" />);
    await screen.findByRole("form", { name: "config editor" });

    // Bump freshness so the sum exceeds 1.0.
    fireEvent.change(screen.getByLabelText("freshness"), {
      target: { value: "0.5" },
    });
    // Provide an actor so only the sum gates the button.
    fireEvent.change(screen.getByLabelText("actor"), {
      target: { value: "alice" },
    });
    expect(screen.getByText(/must equal 1.00/)).toBeTruthy();
    expect(
      (
        screen.getByRole("button", {
          name: "Save new version",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });

  it("saves a valid edit and shows the new version", async () => {
    const saved: ConfigRecord = {
      ...ACTIVE,
      version: 2,
      payload: { ...WEIGHTS, version: "default.v2" },
    };
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(VIEW)) // getConfig
      .mockResolvedValueOnce(json([ACTIVE])) // configHistory
      .mockResolvedValueOnce(json(saved)) // updateConfig
      .mockResolvedValueOnce(
        json({
          profiles: [{ profile: "default", active: saved, versions: [1, 2] }],
        }),
      ) // reload getConfig
      .mockResolvedValueOnce(json([ACTIVE, saved])); // reload configHistory

    render(<ConfigEditor apiKey="admin-key" />);
    await screen.findByRole("form", { name: "config editor" });
    fireEvent.change(screen.getByLabelText("actor"), {
      target: { value: "alice" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save new version" }));

    expect(await screen.findByText(/Saved as version 2/)).toBeTruthy();
    // updateConfig POST should have been sent with the API key + actor.
    const postCall = fetchSpy.mock.calls.find(
      ([, init]) => init?.method === "POST",
    );
    expect(postCall).toBeTruthy();
    const body = JSON.parse(String(postCall?.[1]?.body));
    expect(body.actor).toBe("alice");
  });

  it("surfaces a 422 rejection from the server", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(VIEW))
      .mockResolvedValueOnce(json([ACTIVE]))
      .mockResolvedValueOnce(json({ detail: "bad" }, 422)); // updateConfig rejects

    render(<ConfigEditor apiKey="admin-key" />);
    await screen.findByRole("form", { name: "config editor" });
    fireEvent.change(screen.getByLabelText("actor"), {
      target: { value: "alice" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save new version" }));

    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toMatch(/sum to 1.0/),
    );
  });
});
