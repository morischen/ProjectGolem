/* generated from contracts/verdict.schema.json — DO NOT EDIT (ADR-0004) */

/**
 * Allowed verdict outcomes (base blueprint §9). Insufficient and Mixed are first-class results; the system never forces a conclusion (INV-FORCE).
 */
export type Verdict =
  | "Verified"
  | "Likely True"
  | "Mixed Evidence"
  | "Insufficient Evidence"
  | "Likely False"
  | "False";

/**
 * The deterministic output of the Trust Engine: a verdict with its full, explainable scoring breakdown. Produced only by the deterministic Trust Engine (INV-DETERMINISM); LLMs never generate these values.
 */
export interface TrustResult {
  score: number;
  verdict: Verdict;
  breakdown: ConfidenceBreakdown;
  /**
   * Version of the scoring config that produced this result (reproducibility).
   */
  weights_version: string;
  relevant_count: number;
  supporting_count: number;
  contradicting_count: number;
  /**
   * (support_mass - contradict_mass) / total_mass.
   */
  net_support: number;
  /**
   * minority_mass / total_mass.
   */
  conflict_ratio: number;
}
/**
 * Per-component values (each [0,1]) and the weighted total — full explainability of the score.
 */
export interface ConfidenceBreakdown {
  source_reliability: number;
  corroboration: number;
  evidence_quality: number;
  independence: number;
  freshness: number;
  weighted_total: number;
}
