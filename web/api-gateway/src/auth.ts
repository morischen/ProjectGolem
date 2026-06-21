import { createHash, randomBytes, randomUUID } from "node:crypto";
import type { FastifyReply, FastifyRequest } from "fastify";

export interface ApiKeyRecord {
  scopes: string[];
}
export type ApiKeyMap = Record<string, ApiKeyRecord>;

/**
 * Parse API keys from `EIP_API_KEYS`: entries are `;`-separated, each
 * `key:scope1 scope2`. Example: `EIP_API_KEYS="k1:write read; k2:read"`.
 * Empty/unset → no keys (auth disabled; dev mode).
 */
export function loadApiKeysFromEnv(): ApiKeyMap {
  const raw = process.env.EIP_API_KEYS;
  if (!raw) return {};
  const map: ApiKeyMap = {};
  for (const entry of raw.split(";")) {
    const [key, scopeStr = ""] = entry.split(":");
    const k = key.trim();
    if (!k) continue;
    map[k] = { scopes: scopeStr.trim().split(/\s+/).filter(Boolean) };
  }
  return map;
}

/** Public metadata for a managed key — never includes the secret or its hash. */
export interface KeyMeta {
  id: string;
  label: string;
  scopes: string[];
  prefix: string;
  createdAt: string;
  disabled: boolean;
}

interface KeyEntry {
  meta: KeyMeta;
  keyHash: string;
}

function hashKey(key: string): string {
  return createHash("sha256").update(key).digest("hex");
}

function prefixOf(key: string): string {
  return `${key.slice(0, 6)}…`;
}

/**
 * A managed API-key store (admin portal A4). Keys are held only as SHA-256 hashes;
 * the plaintext is shown once at creation and never persisted. Seeded from the
 * `EIP_API_KEYS` map for backward compatibility, then editable via admin CRUD. This
 * is in-memory (process-local) — a bridge toward a DB-backed store / OIDC later.
 */
export class KeyStore {
  private entries: KeyEntry[] = [];

  constructor(seed: ApiKeyMap = {}) {
    for (const [key, record] of Object.entries(seed)) {
      this.entries.push({
        keyHash: hashKey(key),
        meta: {
          id: randomUUID(),
          label: "seeded",
          scopes: record.scopes,
          prefix: prefixOf(key),
          createdAt: new Date(0).toISOString(),
          disabled: false,
        },
      });
    }
  }

  /** Whether auth is enforced — false (open dev mode) only when no keys exist. */
  enabled(): boolean {
    return this.entries.length > 0;
  }

  /** Resolve a presented key to its scopes, ignoring disabled keys. */
  authenticate(presented: string): ApiKeyRecord | undefined {
    const hash = hashKey(presented);
    const entry = this.entries.find(
      (e) => e.keyHash === hash && !e.meta.disabled,
    );
    return entry ? { scopes: entry.meta.scopes } : undefined;
  }

  list(): KeyMeta[] {
    return this.entries.map((e) => e.meta);
  }

  /** Mint a new key. Returns the plaintext ONCE — it is not recoverable later. */
  create(input: { label: string; scopes: string[] }): {
    plaintext: string;
    meta: KeyMeta;
  } {
    const plaintext = `eip_${randomBytes(24).toString("hex")}`;
    const meta: KeyMeta = {
      id: randomUUID(),
      label: input.label,
      scopes: input.scopes,
      prefix: prefixOf(plaintext),
      createdAt: new Date().toISOString(),
      disabled: false,
    };
    this.entries.push({ keyHash: hashKey(plaintext), meta });
    return { plaintext, meta };
  }

  /** Soft-disable a key (kept for the audit trail). Returns the updated meta. */
  disable(id: string): KeyMeta | undefined {
    const entry = this.entries.find((e) => e.meta.id === id);
    if (!entry) return undefined;
    entry.meta = { ...entry.meta, disabled: true };
    return entry.meta;
  }
}

/**
 * Build a preHandler that enforces an API key carrying `scope`. When the store has
 * no keys, auth is disabled (open dev mode) and the handler is a no-op. A valid key
 * with scope `*` satisfies any scope. 401 = missing/invalid key; 403 = wrong scope.
 */
export function requireScope(store: KeyStore, scope: string) {
  return async (
    request: FastifyRequest,
    reply: FastifyReply,
  ): Promise<void> => {
    if (!store.enabled()) return;
    const header = request.headers["x-api-key"];
    const record =
      typeof header === "string" ? store.authenticate(header) : undefined;
    if (!record) {
      reply.code(401).send({ error: "missing or invalid API key" });
      return;
    }
    if (!record.scopes.includes(scope) && !record.scopes.includes("*")) {
      reply.code(403).send({ error: `insufficient scope (need '${scope}')` });
      return;
    }
  };
}
