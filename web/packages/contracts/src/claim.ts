/* generated from contracts/claim.schema.json — DO NOT EDIT (ADR-0004) */

/**
 * Claim-type taxonomy that drives downstream handling. Empirical claims are verifiable facts; legal/definitional/normative claims are NOT adjudicated as truth by the Trust Engine.
 */
export type ClaimType = "empirical" | "legal" | "definitional" | "predictive" | "normative";

/**
 * A normalized claim object produced by the Claim Engine from raw input (FR-002). Forward contract: defines the shape now so producers/consumers agree; the Claim Engine is a later vertical.
 */
export interface Claim {
  /**
   * Stable identifier of this claim.
   */
  id: string;
  /**
   * Normalized claim statement.
   */
  text: string;
  claim_type: ClaimType;
  /**
   * Entities asserted to act.
   */
  actors?: string[];
  /**
   * Entities asserted to be acted upon.
   */
  targets?: string[];
  /**
   * Events referenced by the claim.
   */
  events?: string[];
  locations?: string[];
  /**
   * Dates/intervals referenced (ISO-8601 where known, else free text).
   */
  dates?: string[];
  /**
   * Atomic assertions extracted from the claim text.
   */
  assertions?: string[];
  /**
   * BCP-47 language tag of the source (e.g. ar, he, en).
   */
  language?: string | null;
  /**
   * Origin URL, if the claim came from a web source.
   */
  source_url?: string | null;
}
