"use client";

import { useState } from "react";

/**
 * Minimal API-key gate for the admin portal. The key carries the `admin` scope and
 * is sent as `x-api-key` on every gateway request (see lib/adminApi). It is held in
 * component state only (not persisted) — refreshing requires re-entry.
 */
export function Login({ onSubmit }: { onSubmit: (apiKey: string) => void }) {
  const [value, setValue] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const key = value.trim();
        if (key) onSubmit(key);
      }}
      aria-label="admin login"
    >
      <h1>EIP Admin</h1>
      <p>Enter an admin API key to browse verdicts.</p>
      <input
        type="password"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="admin API key"
        aria-label="API key"
      />
      <button type="submit" disabled={!value.trim()}>
        Sign in
      </button>
    </form>
  );
}
