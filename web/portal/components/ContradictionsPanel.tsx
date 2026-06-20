import type { Evidence } from "@eip/contracts";

/**
 * Surfaces contradicting evidence as a first-class panel — the platform must make
 * the opposing case easy to find, not bury it (blueprint FR-008 / transparency).
 */
export function ContradictionsPanel({ evidence }: { evidence: Evidence[] }) {
  const contradicting = evidence
    .filter((e) => e.relation === "contradicts")
    .sort((a, b) => b.quality - a.quality);

  return (
    <section aria-label="contradicting evidence">
      <h3>Contradicting evidence ({contradicting.length})</h3>
      {contradicting.length === 0 ? (
        <p>No contradicting evidence on record.</p>
      ) : (
        <ul>
          {contradicting.map((e) => (
            <li key={e.id}>
              {e.source_id} (tier {e.source_tier}) — quality{" "}
              {Math.round(e.quality * 100)}%
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
