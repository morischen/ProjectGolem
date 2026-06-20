/* generated from contracts/evidence.schema.json — DO NOT EDIT (ADR-0004) */

/**
 * How a piece of evidence relates to the claim under assessment.
 */
export type EvidenceRelation = "supports" | "contradicts" | "neutral" | "inconclusive";

/**
 * A single, classified piece of evidence bearing on a claim. quality and freshness are normalized [0,1] signals computed upstream (retrieval/classification); the Trust Engine consumes them as given.
 */
export interface Evidence {
  /**
   * Stable identifier of this evidence item.
   */
  id: string;
  /**
   * Stable id of the originating source, used for independence/corroboration.
   */
  source_id: string;
  /**
   * 1=primary, 2=trusted reporting, 3=context, 4=emerging.
   */
  source_tier: number;
  relation: EvidenceRelation;
  /**
   * Strength of the supporting material.
   */
  quality: number;
  /**
   * Recency, normalized; precomputed upstream.
   */
  freshness: number;
}
