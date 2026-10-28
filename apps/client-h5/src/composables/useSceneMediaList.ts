/**
 * Reviewed public scene media for a list of places.
 *
 * Lists (Search, Map) keep their place identity glyph until the governed
 * public-media endpoint actually returns a `scene_photo`. Private or
 * unreviewed media fails closed and is indistinguishable from "no photo".
 * Requests are de-duplicated and capped so a long list cannot fan out into an
 * unbounded waterfall.
 */
import { ref, watch, type Ref } from "vue";
import { client } from "@petaccess/client-core";
import { firstApprovedSceneMedia } from "../consumer/publicSceneMedia";

export function useSceneMediaList(
  placeIds: Readonly<Ref<string[]>>,
  maxBundles = 3,
  maxPlaces = 12,
): Readonly<Ref<Record<string, string>>> {
  const urls = ref<Record<string, string>>({});
  const requested = new Set<string>();

  const loadOne = async (id: string) => {
    requested.add(id);
    try {
      const events = await client.realityEvents(id);
      const media = await firstApprovedSceneMedia(events, maxBundles);
      if (media?.url) urls.value = { ...urls.value, [id]: media.url };
    } catch {
      // Missing/unreviewed media is an ordinary empty result for a list row.
    }
  };

  watch(
    placeIds,
    (ids) => {
      for (const id of ids.slice(0, maxPlaces)) {
        if (!requested.has(id)) void loadOne(id);
      }
    },
    { immediate: true },
  );

  return urls;
}
