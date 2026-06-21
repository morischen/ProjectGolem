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

/**
 * Build a preHandler that enforces an API key carrying `scope`. When `keys` is
 * empty, auth is disabled (open dev mode) and the handler is a no-op. A valid key
 * with scope `*` satisfies any scope. 401 = missing/invalid key; 403 = wrong scope.
 */
export function requireScope(keys: ApiKeyMap, scope: string) {
  const enabled = Object.keys(keys).length > 0;
  return async (
    request: FastifyRequest,
    reply: FastifyReply,
  ): Promise<void> => {
    if (!enabled) return;
    const header = request.headers["x-api-key"];
    const record = typeof header === "string" ? keys[header] : undefined;
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
