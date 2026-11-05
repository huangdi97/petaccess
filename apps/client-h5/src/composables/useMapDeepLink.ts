/**
 * Exact-ID Place → Map deep-link resolution.
 *
 * This stays separate from the spatial workspace: a place-name search is
 * not authoritative when 20 same-brand branches may share one display name.
 * Route generations also prevent a late A response from selecting A over B.
 */
import { type Ref } from "vue";
import { client, type MapCamera, type PlaceSummary } from "@petaccess/client-core";
import { createEpoch, enrichRows, type RowFacts } from "../consumer/repository";
import { presentDescription } from "../errors";

interface DeepLinkDeps {
  route: { query: { place?: unknown } };
  camera: Ref<MapCamera>;
  places: Ref<PlaceSummary[]>;
  facts: Ref<Map<string, RowFacts>>;
  view: Ref<"map" | "list">;
  isDesktop: Readonly<Ref<boolean>>;
  error: Ref<string>;
  loadNearby: () => Promise<void>;
  select: (place: PlaceSummary) => Promise<void>;
}

export function useMapDeepLink(deps: DeepLinkDeps) {
  const epoch = createEpoch();
  let lastRequestedId: string | null = null;

  function invalidate() {
    epoch.begin();
    lastRequestedId = null;
  }

  function request(id: string) {
    if (id === lastRequestedId) return;
    lastRequestedId = id;
    void focus(id);
  }

  async function focus(id: string) {
    const n = epoch.begin();
    try {
      const target = await client.placeSummary(id);
      if (!epoch.isCurrent(n) || deps.route.query.place !== id) return;

      if (target.latitude != null && target.longitude != null) {
        deps.view.value = "map";
        deps.camera.value = {
          ...deps.camera.value,
          lat: target.latitude,
          lng: target.longitude,
          zoom: Math.max(deps.camera.value.zoom, 15),
        };
        await deps.loadNearby();
        if (!epoch.isCurrent(n) || deps.route.query.place !== id) return;
      }

      const nearby = deps.places.value.find((place) => place.id === id);
      if (!nearby) {
        const additionalFacts = await enrichRows([target]);
        if (!epoch.isCurrent(n) || deps.route.query.place !== id) return;
        deps.places.value = [target, ...deps.places.value];
        deps.facts.value = new Map([...deps.facts.value, ...additionalFacts]);
      }

      if (target.latitude == null || target.longitude == null) {
        deps.view.value = deps.isDesktop.value ? "map" : "list";
        deps.error.value = "该场所缺少可用位置坐标，仅可在列表中查看，未生成地图点位。";
      } else {
        deps.error.value = "";
      }
      await deps.select(nearby ?? target);
    } catch (cause) {
      if (epoch.isCurrent(n) && deps.route.query.place === id) {
        deps.error.value = presentDescription(cause);
        lastRequestedId = null; // permit an explicit subsequent retry
      }
    }
  }

  return { request, invalidate };
}
