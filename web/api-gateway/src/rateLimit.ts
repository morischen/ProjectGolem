import type { FastifyReply, FastifyRequest } from "fastify";

export interface RateLimitOptions {
  limit: number;
  windowMs: number;
  now?: () => number; // injectable clock for deterministic tests
  /** Counter backend. Default: in-memory (per-instance). Inject a shared store
   * (e.g. Redis) for distributed limiting across gateway replicas. */
  store?: RateLimitStore;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;
}

/** Current fixed-window counter state for a key. */
export interface WindowState {
  count: number;
  resetAt: number;
}

/**
 * The counter backend behind the limiter. A single method: atomically register a
 * hit for `key` in the current `windowMs` window and return the resulting count and
 * window reset time. The in-memory default is per-instance; a distributed adapter
 * (Redis `INCR` + `PEXPIRE`, or a sliding-window Lua script) implements this same
 * contract to share counters across gateway replicas (blueprint §22). Keeping it
 * one method means the limiter logic is backend-agnostic and fully unit-testable.
 */
export interface RateLimitStore {
  hit(key: string, windowMs: number, now: number): WindowState;
}

/** Per-instance, in-process fixed-window counter store. */
export class InMemoryRateLimitStore implements RateLimitStore {
  private readonly hits = new Map<string, WindowState>();

  hit(key: string, windowMs: number, now: number): WindowState {
    const entry = this.hits.get(key);
    if (!entry || now >= entry.resetAt) {
      const state = { count: 1, resetAt: now + windowMs };
      this.hits.set(key, state);
      return state;
    }
    entry.count += 1;
    return entry;
  }
}

/** Fixed-window limiter over a pluggable store. Returns a `check(key)` function. */
export function createRateLimiter({
  limit,
  windowMs,
  now = () => Date.now(),
  store = new InMemoryRateLimitStore(),
}: RateLimitOptions) {
  return function check(key: string): RateLimitResult {
    const { count, resetAt } = store.hit(key, windowMs, now());
    if (count > limit) {
      return { allowed: false, remaining: 0, resetAt };
    }
    return { allowed: true, remaining: limit - count, resetAt };
  };
}

/** Build a preHandler that rate-limits by API key (falling back to client IP). */
export function rateLimitHook(options: RateLimitOptions) {
  const check = createRateLimiter(options);
  return async (
    request: FastifyRequest,
    reply: FastifyReply,
  ): Promise<void> => {
    const header = request.headers["x-api-key"];
    const key = (typeof header === "string" && header) || request.ip;
    const result = check(key);
    reply.header("x-ratelimit-remaining", String(result.remaining));
    if (!result.allowed) {
      reply.code(429).send({ error: "rate limit exceeded" });
    }
  };
}
