/**
 * Typed API facade over @petaccess/api-client.
 * The only module in the client allowed to talk HTTP.
 */
import { createClient, ApiError } from "@petaccess/api-client";

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

export interface AnswerCell {
  question: string;
  state: string;
  detail: string;
}

export interface PlaceSummary {
  id: string;
  canonical_name: string;
  place_type: string;
  canonical_address: string | null;
  distance_m: number | null;
}

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
    const res = await api.request<
      Page<{
        id: string;
        display_name: string;
        species: string;
        breed_text: string | null;
        weight_kg: number | null;
        service_role: string;
      }>
    >("get", "/pets");
    return res.items;
  },
  async createPet(body: {
    display_name: string;
    species: string;
    breed_text?: string | null;
    weight_kg?: number | null;
    service_role?: string;
  }) {
    return api.request<{ id: string }>("post", "/pets", { body });
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
    return api.request<{
      id: string;
      canonical_name: string;
      place_type: string;
      canonical_address: string | null;
    }>("get", `/places/${id}`);
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
    proximity_verified?: boolean;
    distance_bucket?: string | null;
    accuracy_bucket?: string | null;
  }) {
    return api.request<{ id: string }>("post", "/observations", { body });
  },
  async verify(body: {
    place_id: string;
    rule_id?: string | null;
    result: string;
    note?: string | null;
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
    return api.request<{ id: string; target_type: string; target_id: string }[]>("get", "/watches");
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
    },
  ) {
    return api.request<EffectiveRuleSet>("post", `/places/${placeId}/effective-rules`, { body });
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
};
