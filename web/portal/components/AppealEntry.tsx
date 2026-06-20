/**
 * Appeal-entry affordance (blueprint FR / appeals process). Presentational for now
 * — wiring to a real appeals endpoint is a later loop. Every appeal is logged
 * publicly, which we state here so the affordance sets the right expectation.
 */
export function AppealEntry({ onAppeal }: { onAppeal?: () => void }) {
  return (
    <section aria-label="appeal">
      <h3>Challenge this verdict</h3>
      <p>
        Submit new evidence, challenge a source, or raise a methodology concern.
        Every appeal is logged publicly.
      </p>
      <button type="button" aria-label="Submit an appeal" onClick={onAppeal}>
        Submit new evidence or an appeal
      </button>
    </section>
  );
}
