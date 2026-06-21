"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AdminApiError,
  configHistory,
  getConfig,
  updateConfig,
  type ConfigRecord,
  type ScoringWeightsPayload,
} from "../lib/adminApi";

type WeightKey =
  | "source_reliability"
  | "corroboration"
  | "evidence_quality"
  | "independence"
  | "freshness";

type ThresholdKey =
  | "strength_floor"
  | "mixed_conflict_threshold"
  | "verified_threshold";

const COMPONENT_WEIGHTS: WeightKey[] = [
  "source_reliability",
  "corroboration",
  "evidence_quality",
  "independence",
  "freshness",
];

const THRESHOLDS: ThresholdKey[] = [
  "strength_floor",
  "mixed_conflict_threshold",
  "verified_threshold",
];

interface FormState {
  source_reliability: number;
  corroboration: number;
  evidence_quality: number;
  independence: number;
  freshness: number;
  tier_reliability: Record<string, number>;
  strength_floor: number;
  mixed_conflict_threshold: number;
  verified_threshold: number;
  actor: string;
  note: string;
}

function formFromPayload(p: ScoringWeightsPayload): FormState {
  return {
    source_reliability: p.source_reliability,
    corroboration: p.corroboration,
    evidence_quality: p.evidence_quality,
    independence: p.independence,
    freshness: p.freshness,
    tier_reliability: { ...p.tier_reliability },
    strength_floor: p.strength_floor,
    mixed_conflict_threshold: p.mixed_conflict_threshold,
    verified_threshold: p.verified_threshold,
    actor: "",
    note: "",
  };
}

/** View + guarded edit of a scoring-config profile, with live sum-to-1 validation. */
export function ConfigEditor({
  apiKey,
  onAuthError,
}: {
  apiKey: string;
  onAuthError?: () => void;
}) {
  const [profile, setProfile] = useState("default");
  const [active, setActive] = useState<ConfigRecord | null>(null);
  const [history, setHistory] = useState<ConfigRecord[]>([]);
  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleAuth = useCallback(
    (err: unknown): boolean => {
      if (
        err instanceof AdminApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        onAuthError?.();
        setError("Access denied — check your admin API key.");
        return true;
      }
      return false;
    },
    [onAuthError],
  );

  const load = useCallback(
    async (p: string) => {
      setError(null);
      try {
        const view = await getConfig(apiKey);
        const entry = view.profiles.find((x) => x.profile === p);
        if (!entry) {
          setError(`No config for profile '${p}'.`);
          return;
        }
        setActive(entry.active);
        setForm(formFromPayload(entry.active.payload));
        setHistory(await configHistory(apiKey, p));
      } catch (err: unknown) {
        if (!handleAuth(err)) setError("Could not load config.");
      }
    },
    [apiKey, handleAuth],
  );

  useEffect(() => {
    void load(profile);
  }, [load, profile]);

  if (error && !form) return <p role="alert">{error}</p>;
  if (form === null) return <p>Loading config…</p>;

  const weightSum = COMPONENT_WEIGHTS.reduce(
    (acc, k) => acc + (form[k] as number),
    0,
  );
  const sumValid = Math.abs(weightSum - 1.0) < 1e-9;
  const canSave = sumValid && form.actor.trim().length > 0;

  function setNum(key: keyof FormState, value: string) {
    setForm((f) => (f ? { ...f, [key]: Number(value) } : f));
  }

  function setTier(tier: string, value: string) {
    setForm((f) =>
      f
        ? {
            ...f,
            tier_reliability: { ...f.tier_reliability, [tier]: Number(value) },
          }
        : f,
    );
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError(null);
    setNotice(null);
    try {
      const record = await updateConfig(apiKey, {
        profile,
        actor: form.actor.trim(),
        note: form.note.trim() || undefined,
        source_reliability: form.source_reliability,
        corroboration: form.corroboration,
        evidence_quality: form.evidence_quality,
        independence: form.independence,
        freshness: form.freshness,
        tier_reliability: form.tier_reliability,
        strength_floor: form.strength_floor,
        mixed_conflict_threshold: form.mixed_conflict_threshold,
        verified_threshold: form.verified_threshold,
      });
      setNotice(
        `Saved as version ${record.version} (${record.payload.version}).`,
      );
      await load(profile);
    } catch (err: unknown) {
      if (handleAuth(err)) return;
      if (err instanceof AdminApiError && err.status === 422) {
        setError(
          "Rejected: component weights must sum to 1.0 (and stay in range).",
        );
      } else {
        setError("Could not save config.");
      }
    }
  }

  return (
    <main>
      <h1>Scoring config</h1>
      <label>
        Profile:{" "}
        <select
          value={profile}
          onChange={(e) => setProfile(e.target.value)}
          aria-label="profile"
        >
          <option value="default">default</option>
          <option value="historical">historical</option>
        </select>
      </label>
      {active && (
        <p>
          Active version <strong>{active.version}</strong> (
          {active.payload.version}){active.actor ? ` — by ${active.actor}` : ""}
        </p>
      )}

      <form onSubmit={save} aria-label="config editor">
        <fieldset>
          <legend>Component weights (must sum to 1.0)</legend>
          {COMPONENT_WEIGHTS.map((k) => (
            <label key={k}>
              {k}{" "}
              <input
                type="number"
                step="0.01"
                value={form[k] as number}
                onChange={(e) => setNum(k, e.target.value)}
                aria-label={k}
              />
            </label>
          ))}
          <p role="status" data-valid={sumValid}>
            Sum: {weightSum.toFixed(2)} {sumValid ? "✓" : "— must equal 1.00"}
          </p>
        </fieldset>

        <fieldset>
          <legend>Source-tier reliability</legend>
          {Object.keys(form.tier_reliability)
            .sort()
            .map((tier) => (
              <label key={tier}>
                tier {tier}{" "}
                <input
                  type="number"
                  step="0.01"
                  value={form.tier_reliability[tier]}
                  onChange={(e) => setTier(tier, e.target.value)}
                  aria-label={`tier ${tier}`}
                />
              </label>
            ))}
        </fieldset>

        <fieldset>
          <legend>Verdict thresholds</legend>
          {THRESHOLDS.map((k) => (
            <label key={k}>
              {k}{" "}
              <input
                type="number"
                step="0.01"
                value={form[k] as number}
                onChange={(e) => setNum(k, e.target.value)}
                aria-label={k}
              />
            </label>
          ))}
        </fieldset>

        <fieldset>
          <legend>Attribution (audited)</legend>
          <label>
            Your name{" "}
            <input
              value={form.actor}
              onChange={(e) =>
                setForm((f) => (f ? { ...f, actor: e.target.value } : f))
              }
              aria-label="actor"
              required
            />
          </label>
          <label>
            Note{" "}
            <input
              value={form.note}
              onChange={(e) =>
                setForm((f) => (f ? { ...f, note: e.target.value } : f))
              }
              aria-label="note"
            />
          </label>
        </fieldset>

        <button type="submit" disabled={!canSave}>
          Save new version
        </button>
      </form>

      {notice && <p role="status">{notice}</p>}
      {error && <p role="alert">{error}</p>}

      <section aria-label="config history">
        <h2>Version history</h2>
        <ol>
          {history.map((h) => (
            <li key={h.version}>
              v{h.version} ({h.payload.version}) — {h.actor ?? "—"}
              {h.note ? `: ${h.note}` : ""} @ {h.knowledge_time}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
