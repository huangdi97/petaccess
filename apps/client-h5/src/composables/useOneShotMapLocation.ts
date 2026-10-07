import { ref, type Ref } from "vue";
import type { LocationState, MapCamera } from "@petaccess/client-core";

interface MapLocationDeps {
  camera: Ref<MapCamera>;
  reload: () => Promise<void>;
}

/** One-shot location only; no continuous tracking or location history. */
export function useOneShotMapLocation(deps: MapLocationDeps) {
  const state = ref<LocationState>("IDLE");

  function locate() {
    if (!("geolocation" in navigator)) {
      state.value = "UNAVAILABLE";
      return;
    }

    state.value = "REQUESTING";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        deps.camera.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          zoom: deps.camera.value.zoom,
        };
        state.value = "GRANTED";
        void deps.reload();
      },
      () => {
        state.value = "DENIED";
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 },
    );
  }

  return { state, locate };
}
