import type {
  ConfidenceBreakdown,
  Evidence,
  TrustResult,
} from "@eip/contracts";

const COMPONENT_LABELS: Record<keyof ConfidenceBreakdown, string> = {
  source_reliability: "Source reliability",
  corroboration: "Corroboration",
  evidence_quality: "Evidence quality",
  independence: "Independence",
  freshness: "Freshness",
  weighted_total: "Weighted total",
};

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/**
 * Read-only transparency surface for a single verdict (blueprint FR-008): the
 * verdict + confidence breakdown, and — deliberately surfaced, not buried — the
 * strongest opposing evidence. Presentation only; never computes a score.
 */
export function VerdictCard({
  result,
  evidence,
}: {
  result: TrustResult;
  evidence: Evidence[];
}) {
  const opposing = [...evidence]
    .filter((e) => e.relation === "contradicts")
    .sort((a, b) => b.quality - a.quality);

  return (
    <section aria-label="verdict">
      <header>
        <h2>{result.verdict}</h2>
        <p>Confidence {pct(result.score)}</p>
        <p>
          {result.supporting_count} supporting · {result.contradicting_count}{" "}
          contradicting · config {result.weights_version}
        </p>
      </header>

      <h3>Confidence breakdown</h3>
      <ul>
        {(Object.keys(COMPONENT_LABELS) as (keyof ConfidenceBreakdown)[]).map(
          (key) => (
            <li key={key}>
              {COMPONENT_LABELS[key]}: {pct(result.breakdown[key])}
            </li>
          ),
        )}
      </ul>

      <h3>Strongest opposing evidence</h3>
      {opposing.length === 0 ? (
        <p>None on record.</p>
      ) : (
        <ul>
          {opposing.map((e) => (
            <li key={e.id}>
              {e.source_id} (tier {e.source_tier}) — quality {pct(e.quality)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
