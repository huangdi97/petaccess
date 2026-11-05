/**
 * Public scene media selection.
 *
 * Only the reviewed public-media endpoint can reveal a media URL. Evidence
 * photos, signage, avatars and import documents are never promoted into venue
 * identity imagery. Missing/denied media is an ordinary empty result.
 */
import {
  client,
  type PublicEvidenceMediaView,
  type RealityEventView,
} from "@petaccess/client-core";

export async function firstApprovedSceneMedia(
  events: RealityEventView[],
  maxBundles = 8,
): Promise<PublicEvidenceMediaView | null> {
  const bundleIds = [
    ...new Set(
      events.map((event) => event.evidence_bundle_id).filter((id): id is string => Boolean(id)),
    ),
  ].slice(0, maxBundles);

  const candidates = await Promise.all(
    bundleIds.map(async (bundleId) => {
      try {
        const media = await client.publicEvidenceMedia(bundleId);
        return media.purpose === "scene_photo" ? media : null;
      } catch {
        // Fail closed: private/unreviewed media is indistinguishable from absent
        // media to the consumer surface.
        return null;
      }
    }),
  );
  // Preserve source order while removing the serial network waterfall.
  return candidates.find((media) => media !== null) ?? null;
}
