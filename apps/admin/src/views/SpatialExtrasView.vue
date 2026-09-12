<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId } from "../api";
import { AMENITY_TYPES, ANIMAL_SCOPES, ENTRANCE_TYPES } from "../v05";

interface Amenity {
  id: string;
  place_id: string;
  zone_id: string | null;
  amenity_type: string;
  status: string;
  source_id: string;
  verified_at: string | null;
}

interface Entrance {
  id: string;
  place_id: string;
  zone_id: string | null;
  name: string;
  entrance_type: string;
  access_notes: string | null;
  source_id: string;
}

interface AccessPath {
  id: string;
  place_id: string;
  name: string;
  from_node: string;
  to_node: string;
  animal_scope: string | null;
  time_window: string | null;
  source_id: string;
}

const amenities = ref<Amenity[]>([]);
const entrances = ref<Entrance[]>([]);
const paths = ref<AccessPath[]>([]);
const error = ref("");
const info = ref("");
const busy = ref("");

const amenityForm = ref({
  place_id: "",
  zone_id: "",
  amenity_type: "water_station",
  status: "available",
  source_id: "",
});

const entranceForm = ref({
  place_id: "",
  zone_id: "",
  name: "",
  entrance_type: "GENERAL",
  location_wkt: "",
  access_notes: "",
  source_id: "",
});

const pathForm = ref({
  place_id: "",
  name: "",
  from_node: "",
  to_node: "",
  stepsJson: "[]",
  animal_scope: "dog",
  time_window: "",
  source_id: "",
});

async function load() {
  error.value = "";
  try {
    const [a, e, p] = await Promise.all([
      page<Amenity>("/admin/amenities", { limit: 50 }),
      page<Entrance>("/admin/entrances", { limit: 50 }),
      page<AccessPath>("/admin/access-paths", { limit: 50 }),
    ]);
    amenities.value = a.items;
    entrances.value = e.items;
    paths.value = p.items;
  } catch (err) {
    error.value = errText(err);
  }
}

async function submit(kind: "amenity" | "entrance" | "path") {
  error.value = "";
  info.value = "";
  busy.value = kind;
  try {
    if (kind === "amenity") {
      const created = await post<{ id: string }>("/admin/amenities", {
        place_id: amenityForm.value.place_id,
        zone_id: amenityForm.value.zone_id || null,
        amenity_type: amenityForm.value.amenity_type,
        status: amenityForm.value.status,
        source_id: amenityForm.value.source_id,
      });
      info.value = `已登记设施 ${created.id.slice(0, 8)}…`;
    } else if (kind === "entrance") {
      const created = await post<{ id: string }>("/admin/entrances", {
        place_id: entranceForm.value.place_id,
        zone_id: entranceForm.value.zone_id || null,
        name: entranceForm.value.name,
        entrance_type: entranceForm.value.entrance_type,
        location_wkt: entranceForm.value.location_wkt || null,
        access_notes: entranceForm.value.access_notes || null,
        source_id: entranceForm.value.source_id,
      });
      info.value = `已登记出入口 ${created.id.slice(0, 8)}…`;
    } else {
      let steps: unknown = null;
      try {
        steps = pathForm.value.stepsJson ? JSON.parse(pathForm.value.stepsJson) : null;
      } catch {
        error.value = "路径步骤 JSON 格式非法";
        busy.value = "";
        return;
      }
      const created = await post<{ id: string }>("/admin/access-paths", {
        place_id: pathForm.value.place_id,
        name: pathForm.value.name,
        from_node: pathForm.value.from_node,
        to_node: pathForm.value.to_node,
        steps,
        animal_scope: pathForm.value.animal_scope,
        time_window: pathForm.value.time_window || null,
        source_id: pathForm.value.source_id,
      });
      info.value = `已登记通行路径 ${created.id.slice(0, 8)}…`;
    }
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

onMounted(load);
</script>

<template>
  <h1>设施 · 出入口 · 通行路径</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="info" class="ok-banner">{{ info }}</div>

  <p class="muted">
    设施与出入口描述的是「场所提供什么」，不是「允不允许」。三者都需携带来源 ID
    —— 高影响规则/事实必须可溯源。经纬度使用 WKT（<span class="mono">POINT(lng lat)</span>）。
  </p>

  <div class="panel">
    <h2>① 设施（Amenity）</h2>
    <div class="row">
      <div class="field"><label>场所 ID</label><input v-model="amenityForm.place_id" class="mono" placeholder="place uuid" /></div>
      <div class="field"><label>分区 ID（可选）</label><input v-model="amenityForm.zone_id" class="mono" placeholder="zone uuid" /></div>
      <div class="field">
        <label>设施类型</label>
        <select v-model="amenityForm.amenity_type">
          <option v-for="t in AMENITY_TYPES" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div class="field">
        <label>状态</label>
        <select v-model="amenityForm.status">
          <option value="available">available（可用）</option>
          <option value="unavailable">unavailable（不可用）</option>
          <option value="unknown">unknown（未知）</option>
        </select>
      </div>
      <div class="field"><label>来源 ID</label><input v-model="amenityForm.source_id" class="mono" placeholder="source uuid" /></div>
    </div>
    <button class="primary" style="margin-top: 10px" :disabled="busy === 'amenity' || !amenityForm.place_id || !amenityForm.source_id" @click="submit('amenity')">
      登记设施
    </button>
  </div>

  <div class="panel">
    <h2>② 出入口（Entrance）</h2>
    <div class="row">
      <div class="field"><label>场所 ID</label><input v-model="entranceForm.place_id" class="mono" placeholder="place uuid" /></div>
      <div class="field"><label>分区 ID（可选）</label><input v-model="entranceForm.zone_id" class="mono" placeholder="zone uuid" /></div>
      <div class="field"><label>名称</label><input v-model="entranceForm.name" placeholder="东门" /></div>
      <div class="field">
        <label>类型</label>
        <select v-model="entranceForm.entrance_type">
          <option v-for="t in ENTRANCE_TYPES" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
    </div>
    <div class="row">
      <div class="field"><label>位置 WKT</label><input v-model="entranceForm.location_wkt" class="mono" placeholder="POINT(116.40 39.90)" /></div>
      <div class="field"><label>通行说明</label><input v-model="entranceForm.access_notes" placeholder="例如：需绕行至北侧" /></div>
      <div class="field"><label>来源 ID</label><input v-model="entranceForm.source_id" class="mono" placeholder="source uuid" /></div>
    </div>
    <button class="primary" style="margin-top: 10px" :disabled="busy === 'entrance' || !entranceForm.place_id || !entranceForm.name || !entranceForm.source_id" @click="submit('entrance')">
      登记出入口
    </button>
    <p class="hint">
      类型含义：GENERAL 通用 / PET_ALLOWED 允许携宠 / PET_PROHIBITED 禁止携宠 / SERVICE_DOG_ONLY 仅服务犬。
    </p>
  </div>

  <div class="panel">
    <h2>③ 通行路径（AccessPath）</h2>
    <div class="row">
      <div class="field"><label>场所 ID</label><input v-model="pathForm.place_id" class="mono" placeholder="place uuid" /></div>
      <div class="field"><label>路径名称</label><input v-model="pathForm.name" placeholder="从东门到宠物区" /></div>
      <div class="field"><label>起点节点</label><input v-model="pathForm.from_node" placeholder="east_gate" /></div>
      <div class="field"><label>终点节点</label><input v-model="pathForm.to_node" placeholder="pet_zone" /></div>
    </div>
    <div class="row">
      <div class="field">
        <label>适用动物</label>
        <select v-model="pathForm.animal_scope">
          <option v-for="a in ANIMAL_SCOPES" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="field"><label>时间窗（可选）</label><input v-model="pathForm.time_window" placeholder="09:00-21:00" /></div>
      <div class="field"><label>来源 ID</label><input v-model="pathForm.source_id" class="mono" placeholder="source uuid" /></div>
    </div>
    <label>路径步骤（JSON 数组）</label>
    <textarea v-model="pathForm.stepsJson" rows="3" class="mono" placeholder='[{"instruction":"乘电梯至 3F"}]' />
    <button class="primary" style="margin-top: 10px" :disabled="busy === 'path' || !pathForm.place_id || !pathForm.name || !pathForm.source_id" @click="submit('path')">
      登记通行路径
    </button>
  </div>

  <div class="panel">
    <h2>已登记设施（{{ amenities.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>场所</th><th>分区</th><th>类型</th><th>状态</th><th>来源</th></tr></thead>
      <tbody>
        <tr v-for="a in amenities" :key="a.id">
          <td class="mono">{{ shortId(a.id) }}</td>
          <td class="mono">{{ shortId(a.place_id) }}</td>
          <td class="mono">{{ shortId(a.zone_id) }}</td>
          <td>{{ a.amenity_type }}</td>
          <td>
            <span class="tag" :class="a.status === 'available' ? 'ok' : a.status === 'unavailable' ? 'restricted' : 'unknown'">
              {{ a.status }}
            </span>
          </td>
          <td class="mono">{{ shortId(a.source_id) }}</td>
        </tr>
        <tr v-if="!amenities.length"><td colspan="6" class="muted">暂无设施记录</td></tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>已登记出入口（{{ entrances.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>场所</th><th>名称</th><th>类型</th><th>通行说明</th><th>来源</th></tr></thead>
      <tbody>
        <tr v-for="e in entrances" :key="e.id">
          <td class="mono">{{ shortId(e.id) }}</td>
          <td class="mono">{{ shortId(e.place_id) }}</td>
          <td>{{ e.name }}</td>
          <td>
            <span class="tag" :class="e.entrance_type === 'PET_ALLOWED' ? 'ok' : e.entrance_type === 'PET_PROHIBITED' ? 'restricted' : 'unknown'">
              {{ e.entrance_type }}
            </span>
          </td>
          <td class="muted">{{ e.access_notes ?? "—" }}</td>
          <td class="mono">{{ shortId(e.source_id) }}</td>
        </tr>
        <tr v-if="!entrances.length"><td colspan="6" class="muted">暂无出入口记录</td></tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>已登记通行路径（{{ paths.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>场所</th><th>名称</th><th>起止节点</th><th>动物</th><th>时间窗</th><th>来源</th></tr></thead>
      <tbody>
        <tr v-for="p in paths" :key="p.id">
          <td class="mono">{{ shortId(p.id) }}</td>
          <td class="mono">{{ shortId(p.place_id) }}</td>
          <td>{{ p.name }}</td>
          <td class="mono">{{ p.from_node }} → {{ p.to_node }}</td>
          <td>{{ p.animal_scope ?? "—" }}</td>
          <td class="muted">{{ p.time_window ?? "—" }}</td>
          <td class="mono">{{ shortId(p.source_id) }}</td>
        </tr>
        <tr v-if="!paths.length"><td colspan="7" class="muted">暂无通行路径记录</td></tr>
      </tbody>
    </table>
  </div>
</template>
