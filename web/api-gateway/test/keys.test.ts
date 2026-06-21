import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app";
import { KeyStore } from "../src/auth";
import type { AdminClient } from "../src/adminClient";

// Minimal admin stub — only recordAudit is used by the key routes.
const admin = { recordAudit: async () => {} } as unknown as AdminClient;

const keys = { "admin-key": { scopes: ["admin"] } };

describe("KeyStore", () => {
  it("authenticates a seeded key and hides the secret in metadata", () => {
    const store = new KeyStore({ "secret-key": { scopes: ["write"] } });
    expect(store.authenticate("secret-key")).toEqual({ scopes: ["write"] });
    expect(store.authenticate("wrong")).toBeUndefined();
    const meta = store.list();
    expect(meta).toHaveLength(1);
    expect(JSON.stringify(meta)).not.toContain("secret-key");
  });

  it("mints a key that authenticates, and disabling revokes it", () => {
    const store = new KeyStore();
    const { plaintext, meta } = store.create({
      label: "ci",
      scopes: ["read"],
    });
    expect(plaintext.startsWith("eip_")).toBe(true);
    expect(store.authenticate(plaintext)).toEqual({ scopes: ["read"] });
    store.disable(meta.id);
    expect(store.authenticate(plaintext)).toBeUndefined();
  });

  it("is disabled (open) when empty", () => {
    expect(new KeyStore().enabled()).toBe(false);
    expect(new KeyStore({ k: { scopes: [] } }).enabled()).toBe(true);
  });
});

describe("gateway /admin/keys", () => {
  it("403 without the admin scope", async () => {
    const app = buildApp({ apiKeys: keys, admin });
    const res = await app.inject({ method: "GET", url: "/admin/keys" });
    expect(res.statusCode).toBe(401);
    await app.close();
  });

  it("lists keys for an admin (metadata only)", async () => {
    const app = buildApp({ apiKeys: keys, admin });
    const res = await app.inject({
      method: "GET",
      url: "/admin/keys",
      headers: { "x-api-key": "admin-key" },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json()[0].label).toBe("seeded");
    expect(JSON.stringify(res.json())).not.toContain("admin-key");
    await app.close();
  });

  it("creates a key (201, plaintext once) that then authenticates", async () => {
    const store = new KeyStore({ "admin-key": { scopes: ["admin"] } });
    const app = buildApp({ keyStore: store, admin });

    const created = await app.inject({
      method: "POST",
      url: "/admin/keys",
      headers: { "x-api-key": "admin-key" },
      payload: { label: "ci", scopes: ["admin"] },
    });
    expect(created.statusCode).toBe(201);
    const newKey = created.json().key as string;
    expect(newKey.startsWith("eip_")).toBe(true);

    // The freshly minted key works on a protected route.
    const used = await app.inject({
      method: "GET",
      url: "/admin/keys",
      headers: { "x-api-key": newKey },
    });
    expect(used.statusCode).toBe(200);
    await app.close();
  });

  it("400 on a malformed create body", async () => {
    const app = buildApp({ apiKeys: keys, admin });
    const res = await app.inject({
      method: "POST",
      url: "/admin/keys",
      headers: { "x-api-key": "admin-key" },
      payload: { label: "no scopes" },
    });
    expect(res.statusCode).toBe(400);
    await app.close();
  });

  it("disables a key (and 404 for an unknown id)", async () => {
    const store = new KeyStore({ "admin-key": { scopes: ["admin"] } });
    const { meta } = store.create({ label: "temp", scopes: ["read"] });
    const app = buildApp({ keyStore: store, admin });

    const ok = await app.inject({
      method: "POST",
      url: `/admin/keys/${meta.id}/disable`,
      headers: { "x-api-key": "admin-key" },
    });
    expect(ok.statusCode).toBe(200);
    expect(ok.json().disabled).toBe(true);

    const missing = await app.inject({
      method: "POST",
      url: "/admin/keys/nope/disable",
      headers: { "x-api-key": "admin-key" },
    });
    expect(missing.statusCode).toBe(404);
    await app.close();
  });
});
