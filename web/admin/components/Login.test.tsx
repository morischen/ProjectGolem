import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Login } from "./Login";

describe("Login", () => {
  it("submits the trimmed API key", () => {
    const onSubmit = vi.fn();
    render(<Login onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("API key"), {
      target: { value: "  admin-key  " },
    });
    fireEvent.submit(screen.getByRole("form", { name: "admin login" }));
    expect(onSubmit).toHaveBeenCalledWith("admin-key");
  });

  it("does not submit an empty key", () => {
    const onSubmit = vi.fn();
    render(<Login onSubmit={onSubmit} />);
    fireEvent.submit(screen.getByRole("form", { name: "admin login" }));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
