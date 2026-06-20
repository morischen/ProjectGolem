import { VerdictCard } from "../components/VerdictCard";
import { sampleEvidence, sampleResult } from "../lib/sample";

export default function Home() {
  return (
    <main>
      <h1>Evidence Intelligence Platform</h1>
      <p>
        The evidence determines the conclusion — never the other way around.
      </p>
      <VerdictCard result={sampleResult} evidence={sampleEvidence} />
    </main>
  );
}
