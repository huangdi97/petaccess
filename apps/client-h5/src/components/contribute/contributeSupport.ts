/**
 * Shared support for the contribution step forms (M7).
 *
 * Proximity buckets (ADR-012: raw GPS never sent — only distance/accuracy
 * buckets) and evidence refs are identical across every form, so they live
 * here instead of drifting per-form.
 */
export function proximity() {
  return { proximity_verified: true, distance_bucket: "<100m", accuracy_bucket: "10-50m" };
}

export function evidenceRefs(mediaId: string | null) {
  return mediaId ? [{ media_id: mediaId, purpose: "signage_evidence" as const }] : null;
}

/** Parent-flow report origin: dated on-site records are `on_site_past`. */
export function reportOrigin(occurredAt: string): "on_site_past" | "on_site_now" {
  const today = new Date().toISOString().slice(0, 10);
  return occurredAt.slice(0, 10) === today ? "on_site_now" : "on_site_past";
}

export function isoAt(date: string): string {
  return new Date(date).toISOString();
}

/** Structured candidate payload keys the backend candidate service reads. */
export function presencePayload(o: {
  animal: string;
  count: string;
  action: string;
  context: string;
}): Record<string, unknown> {
  return {
    animal_scope: o.animal,
    animal_count_estimate: o.count ? Number(o.count) : null,
    observed_action: o.action || "present",
    observed_context: o.context.trim() || null,
  };
}

export function staffPayload(o: {
  action: string;
  awareness: string;
  context: string;
  outcome: string;
}): Record<string, unknown> {
  return {
    actor_role: "unknown_staff",
    trigger_context: o.context.trim() || null,
    response_action: o.action || "unknown",
    staff_awareness_state: o.awareness || "awareness_unknown",
    response_outcome: o.outcome.trim() || null,
  };
}

export function facilityPayload(o: {
  type: string;
  operational: string;
  purpose: string;
  accessMode: string;
  capacity: string;
}): Record<string, unknown> {
  return {
    facility_type: o.type || "other",
    operational_state: o.operational,
    purpose_state: o.purpose || "purpose_unknown",
    access_mode: o.accessMode || "unknown",
    capacity: o.capacity ? Number(o.capacity) : null,
  };
}

/** M7 — dispatch a reality candidate payload by kind (returns payload + animal_scope). */
export function realityPayload(
  kind: "observed_presence" | "staff_response" | "animal_facility",
  f: {
    animal: string;
    count: string;
    action: string;
    context: string;
    staffAction: string;
    staffAwareness: string;
    staffOutcome: string;
    facilityType: string;
    facilityOperational: string;
    facilityPurpose: string;
    facilityAccessMode: string;
    facilityCapacity: string;
  },
): { payload: Record<string, unknown>; animalScope: string | null } {
  if (kind === "observed_presence") {
    return {
      payload: presencePayload({
        animal: f.animal,
        count: f.count,
        action: f.action,
        context: f.context,
      }),
      animalScope: f.animal,
    };
  }
  if (kind === "staff_response") {
    return {
      payload: staffPayload({
        action: f.staffAction,
        awareness: f.staffAwareness,
        context: f.context,
        outcome: f.staffOutcome,
      }),
      animalScope: null,
    };
  }
  return {
    payload: facilityPayload({
      type: f.facilityType,
      operational: f.facilityOperational,
      purpose: f.facilityPurpose,
      accessMode: f.facilityAccessMode,
      capacity: f.facilityCapacity,
    }),
    animalScope: null,
  };
}
