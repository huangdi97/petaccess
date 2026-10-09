/**
 * Zone-scoped access decisions for the Place dossier.
 *
 * A place-level answer is never copied into a zone. Each zone is evaluated
 * with the same current query context plus its own zone_id. Route/context
 * changes invalidate late results so one place or pet cannot overwrite
 * another's zone status.
 */
import { ref, watch, type Ref } from "vue";
import type { AccessAnswer, Zone } from "@petaccess/client-core";
import { createEpoch, currentQueryContext, snapshotFor } from "../consumer/repository";

export interface ZoneDecisionState {
  answer: AccessAnswer | null;
  loading: boolean;
  error: boolean;
}

export function useZoneDecisions(
  placeId: Readonly<Ref<string>>,
  zones: Readonly<Ref<Zone[]>>,
): Readonly<Ref<Record<string, ZoneDecisionState>>> {
  const states = ref<Record<string, ZoneDecisionState>>({});
  const epoch = createEpoch();

  async function refresh() {
    const generation = epoch.begin();
    const id = placeId.value;
    // Route params and the previous place's zones can be reactive in the same
    // tick. Never issue a scoped query with a zone that belongs elsewhere.
    const rows = zones.value.filter((zone) => zone.place_id === id);
    if (!id || !rows.length) {
      states.value = {};
      return;
    }

    states.value = Object.fromEntries(
      rows.map((zone) => [zone.id, { answer: null, loading: true, error: false }]),
    );

    const context = currentQueryContext();
    const results = await Promise.all(
      rows.map(async (zone) => {
        try {
          const { snapshot } = await snapshotFor(id, { ...context, zone_id: zone.id });
          return [zone.id, { answer: snapshot.rule_answer, loading: false, error: false }] as const;
        } catch {
          return [zone.id, { answer: null, loading: false, error: true }] as const;
        }
      }),
    );

    if (!epoch.isCurrent(generation) || placeId.value !== id) return;
    states.value = Object.fromEntries(results);
  }

  watch([placeId, zones, currentQueryContext], () => void refresh(), { immediate: true });
  return states;
}
