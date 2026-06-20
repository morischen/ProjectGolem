import type { Evidence, TrustResult } from "@eip/contracts";

// Sample data for the transparency surface. Real data will come from the gateway
// (a later loop). Typed against the generated contracts so the UI can't drift.

export const sampleEvidence: Evidence[] = [
  {
    id: "e1",
    source_id: "court-record-1",
    source_tier: 1,
    relation: "supports",
    quality: 0.95,
    freshness: 0.9,
  },
  {
    id: "e2",
    source_id: "reuters-1",
    source_tier: 2,
    relation: "supports",
    quality: 0.85,
    freshness: 0.95,
  },
  {
    id: "e3",
    source_id: "ngo-report-1",
    source_tier: 3,
    relation: "contradicts",
    quality: 0.6,
    freshness: 0.7,
  },
];

export const sampleResult: TrustResult = {
  score: 0.78,
  verdict: "Likely True",
  breakdown: {
    source_reliability: 0.8,
    corroboration: 0.75,
    evidence_quality: 0.8,
    independence: 0.67,
    freshness: 0.85,
    weighted_total: 0.78,
  },
  weights_version: "2026-06-19.v0",
  relevant_count: 3,
  supporting_count: 2,
  contradicting_count: 1,
  net_support: 0.55,
  conflict_ratio: 0.22,
};
