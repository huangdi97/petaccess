/**
 * Typed API facade over @petaccess/api-client.
 * The only module in the client allowed to talk HTTP.
 */
import { createClient, ApiError } from "@petaccess/api-client";
import type { ApiSchemas } from "@petaccess/api-client";

let base = "http://127.0.0.1:8000/api/v1";
let tokenProvider: () => string | undefined = () => undefined;
let idemCounter = 0;

export const api = createClient({
  baseUrl: () => base,
  getToken: () => tokenProvider(),
  getIdempotencyKey: () => `cli-${Date.now()}-${idemCounter++}`,
});

export function configureApi(baseUrl: string) {
  base = baseUrl.replace(/\/$/, "");
}

export function setTokenProvider(p: () => string | undefined) {
  tokenProvider = p;
}

export { ApiError };

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ------------------------------------------------------------------ v0.5 types

/** Explainable layered resolution (app.rulespec.v05_resolver.resolve). */
export interface EffectiveRuleSet {
  effect: string;
  compliance_state: "CONSISTENT" | "POTENTIAL_CONFLICT" | "REVIEW_REQUIRED" | "UNKNOWN";
  applicable_rules: string[];
  suppressed: { rule: string; reason: string }[];
  unresolved_conflicts: string[][];
  explanation_steps: string[];
  obligations: string[];
}

/**
 * The unified answer model (design §10). Every consumer surface renders this —
 * none of them re-derives scope, conditions or provenance from the raw rules.
 *
 * `evidence_state` is the part that must not be paraphrased: it is derived on the
 * server from the source row plus the rule's own publication chain, so a
 * government platform relaying the operator can never render as the operator's
 * own confirmation.
 */
export interface AccessAnswerEvidence {
  rule_id: string;
  source_id: string | null;
  source_type: string | null;
  /** Human-adjudicated meaning. `null` when nobody adjudicated that source type —
   *  the UI must then show the raw value rather than invent a sentence. */
  source_type_semantics: string | null;
  issuer: string | null;
  directness: string | null;
  issuer_verification: string | null;
  evidence_strength: string | null;
  source_url: string | null;
  first_party_operator_source_pending: boolean;
  provenance_statement: string;
}

export interface AccessAnswer {
  query_context: Record<string, unknown>;
  normative_result: {
    effect: string;
    compliance_state: string;
    summary: string;
    governing_rule_ids: string[];
    governing_layer: string[];
    mandatory_levels: string[];
  };
  condition_evaluation: {
    conditions: Record<string, unknown>[];
    unmet: unknown[];
    missing_inputs: string[];
    pending_exceptions: string[];
  };
  scope_summary: {
    place: { id: string; name: string; place_type: string };
    zone: { id: string; name: string; zone_type: string } | null;
    zone_requested: boolean;
    /** Which level actually decided the answer — never a flattening. */
    scope_level: "zone" | "place" | "jurisdiction" | "mixed" | "none";
    zone_scoped_rule_count: number;
    animal_scope_requested: string | null;
    declared_role: string | null;
  };
  evidence_state: {
    rules: AccessAnswerEvidence[];
    first_party_operator_source_pending: boolean;
    first_party_operator_source_count: number;
    weakest_directness: string | null;
    acceptance_required: boolean;
  };
  conflict_state: {
    has_conflict: boolean;
    compliance_state: string;
    unresolved_conflicts: string[][];
    suppressed: { rule: string; reason: string }[];
  };
  rights_information: {
    normative_effects: string[];
    operator_obligations: string[];
    facilitation_required: boolean;
    holder_scopes: string[];
  };
  matched_rule_versions: Record<string, unknown>[];
  explanation_items: string[];
  next_actions: string[];
  evaluated_at: string;
  valid_until: string | null;
  valid_from?: string | null;
  evaluation_version: string;
}

export interface BoundaryPreference {
  id?: string;
  attribute: string;
  stance: string;
  note?: string | null;
}

export interface BoundaryProfile {
  id: string;
  user_id?: string;
  name: string;
  is_default: boolean;
  preferences: BoundaryPreference[];
  created_at?: string | null;
}

/** Per-item verdict. Deliberately has no total score (brief §8). */
export interface BoundaryPreferenceResult {
  attribute: string;
  stance: string;
  verdict: "MATCH" | "CONFLICT" | "UNKNOWN";
  reason: string;
}

export interface BoundaryMatchResult {
  profile_id: string;
  results: BoundaryPreferenceResult[];
  summary: { match: number; conflict: number; unknown: number; note: string };
}

/**
 * v0.9-R1 Reality Layer consumer types.
 *
 * Shape mirrors the backend schemas (app/schemas/reality.py) and the
 * coexistence snapshot service (app/services/coexistence_snapshot.py).
 * Reality = what was OBSERVED on site — never a rule, never a score.
 */
export interface StaffResponseSummaryItem {
  response_action: string;
  count: number;
}

export interface FacilitySummaryItem {
  facility_type: string;
  count: number;
  operational_state: string;
  last_verified_at: string | null;
}

export interface RealityAnswer {
  /** One of the six RealitySummary states (OBSERVED_RECENTLY / ... / DISPUTED). */
  state: string;
  last_seen_at: string | null;
  evidence_count: number;
  distinct_source_count: number;
  observed_zones: string[];
  observed_actions: string[];
  staff_response_summary: StaffResponseSummaryItem[];
  facility_summary: FacilitySummaryItem[];
  freshness_state: string | null;
  verification_state: string | null;
  recent_count_7d: number;
  recent_count_30d: number;
  days_since_last_seen: number | null;
  note: string | null;
}

export interface RuleRealityDivergence {
  state: string;
  rule_effect: string;
  reality_state: string;
  note: string;
}

export interface EvidenceSummary {
  rule_evidence: AccessAnswerEvidence[];
  rule_first_party_pending: boolean;
  reality_evidence_count: number;
  reality_distinct_source_count: number;
  reality_verification_state: string | null;
}

export interface CoexistenceSnapshot {
  place_id: string;
  generated_at: string;
  version: string;
  rule_answer: AccessAnswer;
  reality_answer: RealityAnswer;
  staff_response_summary: StaffResponseSummaryItem[];
  facility_summary: FacilitySummaryItem[];
  divergence: RuleRealityDivergence;
  evidence_summary: EvidenceSummary;
}

export interface AnswerCell {
  question: string;
  state: string;
  detail: string;
}

/**
 * Derived from the generated schema, not hand-written.
 *
 * This was a hand-copied interface and it drifted the moment the server grew
 * `parent_place_name` / `matched_alias` / `rule_count` — the API returned them, the
 * type did not mention them, and anything reading them failed to compile. The
 * file header below says business code must never hand-write DTOs (ADR-011);
 * this makes that true for the one place it was not.
 */
export type PlaceSummary = ApiSchemas["PlaceSummary"];

/** Full place record (`GET /places/{id}`), straight from the generated schema. */
export type PlaceDetail = ApiSchemas["PlaceOut"];

export interface Zone {
  id: string;
  place_id: string;
  name: string;
  zone_type: string;
  floor_ref: string | null;
  indoor_outdoor: string;
}

export interface RuleView {
  id: string;
  place_id: string | null;
  zone_id: string | null;
  animal_scope: string;
  action: string;
  effect: string;
  status: string;
  rule_origin: string;
  source_id: string;
  last_verified_at: string | null;
  note: string | null;
  /** normative layer (LEGAL | REGULATORY_GUIDANCE | OPERATOR_POLICY |
   *  TEMPORARY_POLICY); null = legacy row → the resolver flags REVIEW_REQUIRED */
  rule_layer?: string | null;
  /** normative force (mandatory | advisory | operator_discretion) — ADR-023 */
  mandatory_level?: string | null;
}

/** Structured coexistence attribute (spec §2.4 Section 4). Never a judgment. */
export interface CoexistenceItem {
  id: string;
  zone_id: string | null;
  attribute: string;
  value: string;
  conditions: unknown[] | null;
  source_id: string;
  verified_at: string | null;
}

export interface AmenityItem {
  id: string;
  zone_id: string | null;
  amenity_type: string;
  status: string;
  source_id: string;
  verified_at: string | null;
}

export interface EntranceItem {
  id: string;
  zone_id: string | null;
  name: string;
  entrance_type: string;
  access_notes: string | null;
  source_id: string;
}

export interface AccessPathItem {
  id: string;
  name: string;
  from_node: string;
  to_node: string;
  steps: unknown[] | null;
  animal_scope: string | null;
  time_window: Record<string, unknown> | null;
  source_id: string;
}

export interface EventPolicyItem {
  id: string;
  zone_id: string | null;
  name: string;
  animal_scope: string;
  action: string;
  effect: string;
  conditions: unknown[] | null;
  effective_from: string;
  effective_to: string;
  source_id: string;
}

/** Public read-only extras for the Place Detail page (spec §2.4 §4/§5/§6). */
export interface PlaceExtras {
  coexistence: CoexistenceItem[];
  amenities: AmenityItem[];
  entrances: EntranceItem[];
  access_paths: AccessPathItem[];
  event_policies: EventPolicyItem[];
}

export interface EvaluateView {
  status: "MATCH" | "CONDITIONAL" | "RESTRICTED" | "UNKNOWN" | "CONFLICT";
  matched_rules: string[];
  unmet_conditions: { rule_id: string; condition_type: string; kind: string }[];
  unknown_inputs: { input: string; reason: string }[];
  reason_codes: string[];
  source_refs: string[];
}

export interface ObservationView {
  id: string;
  occurred_at: string;
  animal_scope: string;
  observed_action: string;
  staff_action: string;
  place_confidence: string;
  note: string | null;
  dispute_status: string;
}

export interface SourceView {
  id: string;
  source_type: string;
  issuer: string;
  issuer_verification: string;
  collected_at: string;
}

// ------------------------------------------------------------------ pets

/** Pet profile write payload (design #5). `service_role` is user-declared only. */
export interface PetIn {
  display_name: string;
  species: string;
  breed_text?: string | null;
  breed_id?: string | null;
  weight_kg?: number | null;
  shoulder_height_cm?: number | null;
  service_role?: string;
  registration_status?: string | null;
  vaccination_status?: string | null;
  avatar_url?: string | null;
}

export interface PetView {
  id: string;
  display_name: string;
  species: string;
  breed_text: string | null;
  weight_kg: number | null;
  shoulder_height_cm: number | null;
  service_role: string;
  registration_status: string | null;
  vaccination_status: string | null;
  avatar_url: string | null;
  created_at: string;
}

// ----------------------------------------------------------------- media

export type MediaPurposeKey = "signage_evidence" | "scene_photo" | "avatar" | "import_document";

export interface MediaView {
  id: string;
  purpose: string;
  privacy_class: string;
  byte_size: number;
  sha256: string;
  duplicate_of: string | null;
  moderation_status: string;
  expires_at: string | null;
}

export interface MediaMetaView {
  id: string;
  purpose: string;
  privacy_class: string;
  mime_type: string;
  byte_size: number;
  moderation_status: string;
  ocr_text: string | null;
  ocr_rule_candidates: unknown[] | null;
  upload_status: string;
  created_at: string;
  expires_at: string | null;
  deleted_at: string | null;
}

// --------------------------------------------------------------- watches

/** A subscription to changes on a place / zone / rule (notification centre). */
export interface WatchView {
  id: string;
  target_type: string;
  target_id: string;
  channels?: string[];
  status?: string;
  created_at?: string | null;
}

const asParams = (q: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(q).filter(([, v]) => v !== undefined)) as Record<
    string,
    string | number | boolean
  >;

export const client = {
  async register(displayName: string, email: string, password: string) {
    return api.request<{ access_token: string }>("post", "/auth/register", {
      body: { display_name: displayName, email, password },
    });
  },
  async login(email: string, password: string) {
    return api.request<{ access_token: string }>("post", "/auth/login", {
      body: { email, password },
    });
  },
  async me() {
    return api.request<{ id: string; display_name: string; email: string | null; role: string }>(
      "get",
      "/auth/me",
    );
  },

  async myPets() {
    const res = await api.request<Page<PetView>>("get", "/pets");
    return res.items;
  },
  async createPet(body: PetIn) {
    return api.request<PetView>("post", "/pets", { body });
  },
  async updatePet(petId: string, body: PetIn) {
    return api.request<PetView>("patch", `/pets/${petId}`, { body });
  },
  async deletePet(petId: string) {
    return api.request<void>("delete", `/pets/${petId}`);
  },

  // --------------------------------------------------------------- media
  // Multipart upload cannot go through the JSON-only api-client, so this is
  // the one method that talks fetch directly. It still uses the shared base
  // URL and token provider, so auth/error semantics stay identical.

  async uploadMedia(
    file: File,
    purpose: MediaPurposeKey,
    opts: { ownerType?: string; ownerId?: string } = {},
  ): Promise<MediaView> {
    const form = new FormData();
    form.append("file", file);
    const query = new URLSearchParams({ purpose });
    if (opts.ownerType) query.set("owner_type", opts.ownerType);
    if (opts.ownerId) query.set("owner_id", opts.ownerId);
    const token = tokenProvider();
    const res = await fetch(`${base}/media/upload?${query.toString()}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    const payload = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    if (!res.ok) {
      const err = payload.error as { code?: string; message?: string } | undefined;
      throw new ApiError(res.status, err?.code ?? "upload_failed", err?.message ?? "上传失败");
    }
    return payload as unknown as MediaView;
  },
  async mediaUrl(mediaId: string) {
    return api.request<{ id: string; url: string; expires_in: number }>(
      "get",
      `/media/${mediaId}/url`,
    );
  },
  async mediaMeta(mediaId: string) {
    return api.request<MediaMetaView>("get", `/media/${mediaId}`);
  },
  async deleteMedia(mediaId: string) {
    return api.request<void>("delete", `/media/${mediaId}`);
  },

  async searchPlaces(q: string) {
    const res = await api.request<Page<PlaceSummary>>("get", "/places", {
      query: asParams({ q, limit: 20 }),
    });
    return res.items;
  },
  async nearby(lat: number, lng: number, radiusM = 2000) {
    const res = await api.request<Page<PlaceSummary>>("get", "/places/nearby", {
      query: asParams({ lat, lng, radius_m: radiusM, limit: 30 }),
    });
    return res.items;
  },
  async place(id: string) {
    // Derived, not hand-written — same reason as `PlaceSummary` above. The
    // hand-written copy here had already lost `parent_place_id`,
    // `lifecycle_status` and the audit timestamps, so anything wanting them
    // had to re-declare the shape locally (PlaceView did).
    return api.request<PlaceDetail>("get", `/places/${id}`);
  },
  async zones(placeId: string) {
    return api.request<Zone[]>("get", `/places/${placeId}/zones`);
  },
  async zoneGeometries(zoneId: string) {
    return api.request<{ id: string; geojson: { type: string; coordinates: unknown }[] }>(
      "get",
      `/zones/${zoneId}/geometries`,
    );
  },
  async placeGeometries(placeId: string) {
    return api.request<{ id: string; geojson: { type: string; coordinates: unknown }[] }>(
      "get",
      `/places/${placeId}/geometries`,
    );
  },
  async rules(placeId: string) {
    const res = await api.request<Page<RuleView>>("get", `/places/${placeId}/rules`);
    return res.items;
  },
  async evaluate(body: {
    animal: { species: string; service_role?: string; weight_kg?: number | null };
    place_id: string;
    zone_id?: string | null;
    intended_action?: string;
  }) {
    return api.request<EvaluateView>("post", "/rules/evaluate", { body });
  },
  async observations(placeId: string) {
    const res = await api.request<Page<ObservationView>>("get", `/places/${placeId}/observations`);
    return res.items;
  },
  async createObservation(body: {
    place_id: string;
    zone_id?: string | null;
    occurred_at: string;
    occurred_precision: string;
    animal_scope: string;
    observed_action: string;
    staff_action: string;
    place_confidence: string;
    note?: string | null;
    evidence_refs?: { media_id: string; purpose?: string }[] | null;
    proximity_verified?: boolean;
    distance_bucket?: string | null;
    accuracy_bucket?: string | null;
  }) {
    return api.request<{ id: string }>("post", "/observations", { body });
  },
  async verify(body: {
    place_id: string;
    zone_id?: string | null;
    rule_id?: string | null;
    event_type?: string;
    result: string;
    note?: string | null;
    evidence_refs?: { media_id: string; purpose?: string }[] | null;
    proximity_verified?: boolean;
    distance_bucket?: string | null;
    accuracy_bucket?: string | null;
  }) {
    return api.request<{ id: string }>("post", "/verifications", { body });
  },
  async verifications(placeId: string) {
    const res = await api.request<
      Page<{
        id: string;
        event_type: string;
        result: string;
        occurred_at: string;
        note: string | null;
      }>
    >("get", `/places/${placeId}/verifications`);
    return res.items;
  },
  async watch(targetType: string, targetId: string) {
    return api.request<{ id: string }>("post", "/watches", {
      body: { target_type: targetType, target_id: targetId, channels: ["in_app"] },
    });
  },
  async unwatch(watchId: string) {
    return api.request<void>("delete", `/watches/${watchId}`);
  },
  async myWatches() {
    return api.request<WatchView[]>("get", "/watches");
  },
  async regulations(placeId?: string) {
    const path = placeId ? `/places/${placeId}/regulations` : "/regulations";
    const res = await api.request<
      Page<{
        id: string;
        document_name: string;
        clause_ref: string | null;
        review_status: string;
        effect: string | null;
      }>
    >("get", path);
    return res.items;
  },
  async allSources() {
    const res = await api.request<
      Page<{
        id: string;
        source_type: string;
        issuer: string;
        issuer_verification: string;
        collected_at: string;
      }>
    >("get", "/sources");
    return res.items;
  },
  async submitDispute(body: {
    target_type: string;
    target_id: string;
    reason_code: string;
    notice_text: string;
  }) {
    return api.request<{ id: string }>("post", "/disputes", { body });
  },
  async submitClaim(body: {
    place_id: string;
    operator_id: string;
    verification_method: string;
    evidence_refs?: Record<string, unknown> | null;
  }) {
    return api.request<{ id: string }>("post", "/operator-claims", { body });
  },
  async submitOperatorRules(claimId: string, answers: unknown[]) {
    return api.request<{ created_rules: string[] }>(
      "post",
      `/operator-claims/${claimId}/questionnaire`,
      { body: { answers } },
    );
  },
  async mapConfig() {
    return api.request<{ provider: string; center: { lat: number; lng: number }; zoom: number }>(
      "get",
      "/ai/map/config",
    );
  },

  // ------------------------------------------------------------- v0.5 domain
  // These back the v0.5 H5 surfaces: explainable effective rules, the user's
  // own coexistence boundary, and the per-item boundary match.

  async effectiveRules(
    placeId: string,
    body: {
      animal: string;
      service_role?: string;
      action?: string;
      zone_id?: string | null;
      // ADR-025: pin the query to one precise animal role so a hearing-dog
      // question never inherits a guide-dog proviso. Omit it and a generic
      // service-dog query expands to the whole assistance group (query-side only).
      declared_role?: string | null;
    },
  ) {
    return api.request<EffectiveRuleSet>("post", `/places/${placeId}/effective-rules`, { body });
  },
  /**
   * The unified answer model — the surface-facing call.
   *
   * Prefer this over `effectiveRules` for anything a reader sees: it carries the
   * scope level that actually governs, the condition evaluation, and the
   * provenance (`evidence_state`) that `effectiveRules` deliberately omits.
   */
  async accessAnswer(
    placeId: string,
    body: {
      animal: string;
      service_role?: string;
      action?: string;
      zone_id?: string | null;
      declared_role?: string | null;
      /** ADR-031: ephemeral, read for this request and never stored. Omitting it
       *  does not mean "no" — the answer comes back `conditional` with
       *  `missing_inputs` instead. */
      holder_scopes?: string[];
    },
  ) {
    return api.request<AccessAnswer>("post", `/places/${placeId}/access-answer`, { body });
  },
  /**
   * v0.9-R1: a signed-in visitor contributes an on-site reality fact (§25.2).
   * Lands as a REVIEW_PENDING candidate; AI never sets reality_decision.
   */
  async submitRealityContribution(
    placeId: string,
    body: {
      candidate_type: "observed_presence" | "staff_response" | "animal_facility";
      zone_id?: string | null;
      animal_scope?: string | null;
      observed_at?: string | null;
      payload?: Record<string, unknown> | null;
    },
  ) {
    return api.request<{ id: string }>("post", `/places/${placeId}/reality/contributions`, {
      body,
    });
  },
  async boundaryProfiles() {
    return api.request<{ items: BoundaryProfile[] }>("get", "/boundary-profiles");
  },
  async defaultBoundaryProfile() {
    return api.request<{ profile: BoundaryProfile | null }>("get", "/boundary-profiles/default");
  },
  async saveBoundaryProfile(body: {
    name: string;
    is_default?: boolean;
    preferences: { attribute: string; stance: string; note?: string | null }[];
  }) {
    return api.request<BoundaryProfile>("put", "/boundary-profiles/default", { body });
  },
  async boundaryMatch(placeId: string) {
    return api.request<BoundaryMatchResult>("get", `/places/${placeId}/boundary-match`);
  },
  async answerability(placeId: string) {
    return api.request<{ place_id: string; cells: AnswerCell[] }>(
      "get",
      `/places/${placeId}/answerability`,
    );
  },
  async placeExtras(placeId: string) {
    return api.request<PlaceExtras>("get", `/places/${placeId}/extras`);
  },
  async placeReality(placeId: string) {
    return api.request<RealityAnswer>("get", `/places/${placeId}/reality`);
  },
  /**
   * CoexistenceSnapshot — the ONE aggregate every consumer surface reads
   * (v0.9 §9 / AC9). Home / Search / Map / Place must call this instead of
   * recomputing rule or reality themselves.
   */
  async coexistenceSnapshot(
    placeId: string,
    body: {
      animal?: string;
      service_role?: string;
      action?: string;
      zone_id?: string | null;
      declared_role?: string | null;
      holder_scopes?: string[];
    } = {},
  ) {
    return api.request<CoexistenceSnapshot>("post", `/places/${placeId}/coexistence`, { body });
  },
};
