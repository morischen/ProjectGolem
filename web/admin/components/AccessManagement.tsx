"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AdminApiError,
  createKey,
  disableKey,
  listKeys,
  type KeyMeta,
} from "../lib/adminApi";

const SCOPES = ["read", "write", "admin"];

/** Manage API keys/roles (A4). Keys are shown by prefix only; the secret appears
 * once at creation and is never recoverable. */
export function AccessManagement({
  apiKey,
  onAuthError,
}: {
  apiKey: string;
  onAuthError?: () => void;
}) {
  const [keys, setKeys] = useState<KeyMeta[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [label, setLabel] = useState("");
  const [scopes, setScopes] = useState<string[]>(["read"]);
  const [newSecret, setNewSecret] = useState<string | null>(null);

  const handleAuth = useCallback(
    (err: unknown): boolean => {
      if (
        err instanceof AdminApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        onAuthError?.();
        setError("Access denied — check your admin API key.");
        return true;
      }
      return false;
    },
    [onAuthError],
  );

  const load = useCallback(async () => {
    setError(null);
    try {
      setKeys(await listKeys(apiKey));
    } catch (err: unknown) {
      if (!handleAuth(err)) setError("Could not load keys.");
    }
  }, [apiKey, handleAuth]);

  useEffect(() => {
    void load();
  }, [load]);

  function toggleScope(scope: string) {
    setScopes((s) =>
      s.includes(scope) ? s.filter((x) => x !== scope) : [...s, scope],
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNewSecret(null);
    try {
      const { key } = await createKey(apiKey, { label: label.trim(), scopes });
      setNewSecret(key);
      setLabel("");
      await load();
    } catch (err: unknown) {
      if (!handleAuth(err)) setError("Could not create the key.");
    }
  }

  async function revoke(id: string) {
    setError(null);
    try {
      await disableKey(apiKey, id);
      await load();
    } catch (err: unknown) {
      if (!handleAuth(err)) setError("Could not revoke the key.");
    }
  }

  if (error && !keys) return <p role="alert">{error}</p>;
  if (keys === null) return <p>Loading keys…</p>;

  const canCreate = label.trim().length > 0 && scopes.length > 0;

  return (
    <main>
      <h1>Access management</h1>

      <form onSubmit={submit} aria-label="create key">
        <h2>Create a key</h2>
        <label>
          Label{" "}
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            aria-label="key label"
            required
          />
        </label>
        <fieldset>
          <legend>Scopes</legend>
          {SCOPES.map((s) => (
            <label key={s}>
              <input
                type="checkbox"
                checked={scopes.includes(s)}
                onChange={() => toggleScope(s)}
                aria-label={`scope ${s}`}
              />
              {s}
            </label>
          ))}
        </fieldset>
        <button type="submit" disabled={!canCreate}>
          Create key
        </button>
      </form>

      {newSecret && (
        <p role="status">
          New key (copy it now — shown once): <code>{newSecret}</code>
        </p>
      )}
      {error && <p role="alert">{error}</p>}

      <section aria-label="keys">
        <h2>Keys ({keys.length})</h2>
        <table>
          <thead>
            <tr>
              <th>Label</th>
              <th>Prefix</th>
              <th>Scopes</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id}>
                <td>{k.label}</td>
                <td>
                  <code>{k.prefix}</code>
                </td>
                <td>{k.scopes.join(", ")}</td>
                <td>{k.disabled ? "disabled" : "active"}</td>
                <td>
                  {!k.disabled && (
                    <button type="button" onClick={() => revoke(k.id)}>
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
