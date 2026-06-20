import { VerdictCard } from "../components/VerdictCard";
import { fetchVerdict } from "../lib/gateway";

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
    </main>
  );
}
