/**
 * One vocabulary for enum values that reach the screen.
 *
 * Raw enum strings were leaking into the UI (`residential_community` rendered
 * verbatim on search results), which reads as an internal id rather than a
 * product. Client H5 and Admin share this map so the same place type is never
 * named two different ways in two tabs.
 *
 * Lookups are total-by-fallback: an enum value added on the server before this
 * map catches up shows the raw value instead of blanking the row.
 */

export const PLACE_TYPE_LABELS: Record<string, string> = {
  restaurant: "餐饮",
  cafe: "咖啡",
  mall: "商场",
  store: "店铺",
  hotel: "酒店",
  park: "公园",
  square: "广场",
  greenway: "绿道",
  beach: "海滩",
  scenic_area: "景区",
  residential_community: "住宅小区",
  office_campus: "办公园区",
  hospital: "医院",
  school: "学校",
  library: "图书馆",
  museum: "博物馆",
  sports_venue: "运动场馆",
  transport_hub: "交通枢纽",
  other: "其他",
};

export function placeTypeLabel(value: string | null | undefined): string {
  if (!value) return "";
  return PLACE_TYPE_LABELS[value] ?? value;
}

/**
 * Freshness in words, not a timestamp dump.
 *
 * Deliberately coarse: "3 天前" invites the reader to treat recency as quality,
 * and rule material does not rot on that schedule. What matters is whether the
 * user is looking at something verified this quarter or something from the
 * archive.
 */
export function freshnessLabel(iso: string | null | undefined, now = new Date()): string {
  if (!iso) return "尚未核验";
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "核验时间未知";
  const days = Math.floor((now.getTime() - then.getTime()) / 86_400_000);
  if (days < 0) return "核验时间异常";
  if (days === 0) return "今日核验";
  if (days < 30) return `${days} 天前核验`;
  if (days < 365) return `${Math.floor(days / 30)} 个月前核验`;
  return `${Math.floor(days / 365)} 年前核验`;
}
