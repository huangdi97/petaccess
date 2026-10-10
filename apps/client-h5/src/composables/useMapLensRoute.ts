/** Keep the four map lenses in URL history without changing server facts. */
import { watch, type Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { parseMapLens, type MapLensKey } from "../consumer/mapLens";

export function useMapLensRoute(lens: Ref<MapLensKey>, activeFilters: Ref<string[]>) {
  const route = useRoute();
  const router = useRouter();

  watch(lens, (value) => {
    activeFilters.value = [];
    const routeValue = typeof route.query.lens === "string" ? route.query.lens : "rule";
    if (routeValue === value || (value === "rule" && routeValue === "rule")) return;
    void router.replace({
      query: { ...route.query, lens: value === "rule" ? undefined : value },
    });
  });

  watch(
    () => route.query.lens,
    (value) => {
      const next = parseMapLens(value);
      if (next !== lens.value) lens.value = next;
    },
  );
}
