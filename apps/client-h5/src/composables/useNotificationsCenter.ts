import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  client,
  session,
  type WatchEventView,
  type WatchView,
} from "@petaccess/client-core";
import { presentDescription } from "../errors";

const TARGET_LABELS: Record<string, string> = {
  place: "场所",
  zone: "区域",
  rule: "具体规则",
};

export function useNotificationsCenter() {
  const router = useRouter();
  const watches = ref<WatchView[]>([]);
  const events = ref<WatchEventView[]>([]);
  const targetNames = ref<Record<string, string>>({});
  const loading = ref(true);
  const error = ref("");
  const actionError = ref("");
  const unsubscribing = ref<string | null>(null);
  const signedIn = ref(false);

  const activeRuleCount = computed(
    () => watches.value.filter((watch) => watch.watch_domain === "rule").length,
  );
  const activeRealityCount = computed(
    () => watches.value.filter((watch) => watch.watch_domain === "reality").length,
  );

  function domainLabel(watch: WatchView): string {
    return watch.watch_domain === "reality" ? "现场更新" : "规则变化";
  }

  function targetLabel(watch: WatchView): string {
    return (
      targetNames.value[watch.target_id] ??
      TARGET_LABELS[watch.target_type] ??
      "关注对象"
    );
  }

  function eventPlaceLabel(event: WatchEventView): string {
    return event.place_id
      ? (targetNames.value[event.place_id] ?? "场所变化")
      : "规则变化";
  }

  function eventTypeLabel(event: WatchEventView): string {
    switch (event.event_type) {
      case "rule_version_published":
        return "正式规则已更新";
      case "rule_exception_published":
        return "规则适用边界已更新";
      case "reality_observed_presence_published":
        return "新增经核验的动物出现记录";
      case "reality_staff_response_published":
        return "新增经核验的工作人员处理记录";
      case "reality_animal_facility_published":
        return "动物设施事实已更新";
    }
  }

  function eventDetail(event: WatchEventView): string {
    return event.watch_domain === "reality"
      ? "这是一条经人工核验后发布的现场事实，不代表正式准入规则发生变化。"
      : "这是一条经过审核并发布的规则变化；可进入详情查看适用对象、区域与来源。";
  }

  function eventTime(event: WatchEventView): string {
    return new Intl.DateTimeFormat("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(event.occurred_at));
  }

  async function openEvent(event: WatchEventView) {
    if (!event.read_at) {
      void client
        .markWatchEventRead(event.id)
        .then((updated) => {
          const index = events.value.findIndex((item) => item.id === updated.id);
          if (index >= 0) events.value[index] = updated;
        })
        .catch(() => {
          // A read-receipt failure must never block the published fact.
        });
    }
    if (!event.place_id) return;
    if (event.watch_domain === "reality") {
      await router.push({ name: "reality-trace", params: { id: event.place_id } });
      return;
    }
    await router.push({
      name: "place",
      params: { id: event.place_id },
      query: { view: "rules" },
    });
  }

  async function load() {
    loading.value = true;
    error.value = "";
    actionError.value = "";
    watches.value = [];
    events.value = [];
    targetNames.value = {};
    try {
      await session.restore();
      signedIn.value = session.signedIn;
      if (signedIn.value) {
        const [nextWatches, nextEvents] = await Promise.all([
          client.myWatches(),
          client.myWatchEvents(),
        ]);
        watches.value = nextWatches;
        events.value = nextEvents;
      }
      const placeIds = [
        ...new Set([
          ...watches.value
            .filter((watch) => watch.target_type === "place")
            .map((watch) => watch.target_id),
          ...events.value
            .map((event) => event.place_id)
            .filter((id): id is string => Boolean(id)),
        ]),
      ];
      const names = await Promise.all(
        placeIds.map(async (id) => {
          const place = await client.place(id).catch(() => null);
          return [id, place?.canonical_name ?? "场所名称待补充"] as const;
        }),
      );
      targetNames.value = Object.fromEntries(names);
    } catch (cause) {
      error.value = presentDescription(cause);
    } finally {
      loading.value = false;
    }
  }

  async function unsubscribe(watch: WatchView) {
    if (unsubscribing.value) return;
    unsubscribing.value = watch.id;
    actionError.value = "";
    try {
      await client.unwatch(watch.id);
      watches.value = watches.value.filter((item) => item.id !== watch.id);
    } catch (cause) {
      actionError.value = presentDescription(cause);
    } finally {
      unsubscribing.value = null;
    }
  }

  function goLogin() {
    return router.push({ name: "onboarding", query: { next: "/notifications" } });
  }

  function goHome() {
    return router.push({ name: "home" });
  }

  onMounted(load);

  return {
    watches,
    events,
    loading,
    error,
    actionError,
    unsubscribing,
    signedIn,
    activeRuleCount,
    activeRealityCount,
    domainLabel,
    targetLabel,
    eventPlaceLabel,
    eventTypeLabel,
    eventDetail,
    eventTime,
    openEvent,
    load,
    unsubscribe,
    goLogin,
    goHome,
  };
}
