import { AppealEntry } from "../components/AppealEntry";
import { ContradictionsPanel } from "../components/ContradictionsPanel";
import { VerdictCard } from "../components/VerdictCard";
import { fetchVerdict } from "../lib/gateway";

// Render per-request so production builds fetch live verdicts too (not just `next
// dev`). Without this, `next build` would statically prerender with whatever it
// fetched at build time (i.e. the sample fallback).
export const dynamic = "force-dynamic";

export default async function Home() {
  const { result, evidence, live } = await fetchVerdict();

  return (
    <main>
      <h1>Evidence Intelligence Platform</h1>
      <p>
        The evidence determines the conclusion — never the other way around.
      </p>
      <p>
        <small>
          {live
            ? "Live verdict from gateway"
            : "Sample data (gateway unavailable)"}
        </small>
      </p>
      <VerdictCard result={result} evidence={evidence} />
      <ContradictionsPanel evidence={evidence} />
      <AppealEntry />
    </main>
  );
}
