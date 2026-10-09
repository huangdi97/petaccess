/**
 * Load a reviewed public scene photo for the currently selected place.
 *
 * Route/selection changes invalidate late responses. The public-media endpoint
 * remains the authorization boundary; private evidence and non-scene media are
 * never exposed as venue identity imagery.
 */
import { ref, watch, type Readonly, type Ref } from "vue";
import { client, type PublicEvidenceMediaView } from "@petaccess/client-core";
import { createEpoch } from "../consumer/repository";
import { firstApprovedSceneMedia } from "../consumer/publicSceneMedia";

export function usePlaceSceneMedia(
  placeId: Readonly<Ref<string | null>>,
  maxBundles = 4,
): Readonly<Ref<PublicEvidenceMediaView | null>> {
  const media = ref<PublicEvidenceMediaView | null>(null);
  const epoch = createEpoch();

  watch(
    placeId,
    (id) => {
      const generation = epoch.begin();
      media.value = null;
      if (!id) return;

      void (async () => {
        try {
          const events = await client.realityEvents(id);
          if (!epoch.isCurrent(generation)) return;
          const next = await firstApprovedSceneMedia(events, maxBundles);
          if (!epoch.isCurrent(generation)) return;
          media.value = next;
        } catch {
          if (epoch.isCurrent(generation)) media.value = null;
        }
      })();
    },
    { immediate: true },
  );

  return media;
}
