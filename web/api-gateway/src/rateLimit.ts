import type { FastifyReply, FastifyRequest } from "fastify";

export interface RateLimitOptions {
  limit: number;
  windowMs: number;
  now?: () => number; // injectable clock for deterministic tests
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;
}

/** Fixed-window in-memory limiter. Returns a `check(key)` function. */
export function createRateLimiter({
  limit,
  windowMs,
  now = () => Date.now(),
}: RateLimitOptions) {
  const hits = new Map<string, { count: number; resetAt: number }>();
  return function check(key: string): RateLimitResult {
    const t = now();
    const entry = hits.get(key);
    if (!entry || t >= entry.resetAt) {
      const resetAt = t + windowMs;
      hits.set(key, { count: 1, resetAt });
      return { allowed: true, remaining: limit - 1, resetAt };
    }
    if (entry.count >= limit) {
      return { allowed: false, remaining: 0, resetAt: entry.resetAt };
    }
    entry.count += 1;
    return {
      allowed: true,
      remaining: limit - entry.count,
      resetAt: entry.resetAt,
    };
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
