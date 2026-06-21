"use client";

import { useCallback, useEffect, useState } from "react";
import { AdminApiError, getMetrics, type MetricsView } from "../lib/adminApi";

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

/** Calibration/accuracy + review-queue health dashboard (the §23/§26 gate metrics). */
export function Dashboard({
  apiKey,
  onAuthError,
}: {
  apiKey: string;
  onAuthError?: () => void;
}) {
  const [metrics, setMetrics] = useState<MetricsView | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setMetrics(await getMetrics(apiKey));
    } catch (err: unknown) {
      if (
        err instanceof AdminApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        onAuthError?.();
        setError("Access denied — check your admin API key.");
      } else {
        setError("Could not load metrics.");
      }
    }
  }, [apiKey, onAuthError]);

  useEffect(() => {
    void load();
  }, [load]);

  if (error) return <p role="alert">{error}</p>;
  if (metrics === null) return <p>Loading metrics…</p>;

  const { benchmark, queue, claims_count } = metrics;

  return (
    <main>
      <h1>Dashboard</h1>

      <section aria-label="benchmark">
        <h2>Calibration (gold benchmark)</h2>
        {benchmark === null ? (
          <p>Benchmark unavailable.</p>
        ) : (
          <dl>
            <dt>Verdict accuracy</dt>
            <dd>{pct(benchmark.verdict_accuracy)}</dd>
            <dt>Calibration error (ECE)</dt>
            <dd>{benchmark.calibration_error.toFixed(3)}</dd>
            <dt>Cases</dt>
            <dd>{benchmark.total}</dd>
            <dt>By difficulty</dt>
            <dd>
              <ul>
                {Object.entries(benchmark.by_difficulty).map(([k, v]) => (
                  <li key={k}>
                    {k}: {pct(v)}
                  </li>
                ))}
              </ul>
            </dd>
          </dl>
        )}
      </section>

      <section aria-label="queue health">
        <h2>Review queue</h2>
        <dl>
          <dt>Open</dt>
          <dd>{queue.open}</dd>
          <dt>Resolved</dt>
          <dd>{queue.resolved}</dd>
          <dt>By kind</dt>
          <dd>
            <ul>
              {Object.entries(queue.by_kind).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </dd>
        </dl>
      </section>

      <section aria-label="corpus">
        <h2>Corpus</h2>
        <p>Claims with verdicts: {claims_count}</p>
      </section>
    </main>
  );
}
