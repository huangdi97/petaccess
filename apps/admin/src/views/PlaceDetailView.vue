<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { get, post, ApiError } from "../api";

interface Zone {
  id: string;
  name: string;
  zone_type: string;
  floor_ref: string | null;
  indoor_outdoor: string;
}
interface Rule {
  id: string;
  zone_id: string | null;
  animal_scope: string;
  action: string;
  effect: string;
  status: string;
  source_id: string;
  rule_origin: string;
}
interface Geometry {
  id: string;
  zone_id: string | null;
  geometry_type: string;
  precision: string;
}

const route = useRoute();
const placeId = route.params.id as string;
const place = ref<{
  canonical_name: string;
  place_type: string;
  canonical_address: string | null;
} | null>(null);
const zones = ref<Zone[]>([]);
const rules = ref<Rule[]>([]);
const geometries = ref<Geometry[]>([]);
const error = ref("");

const zoneForm = ref({ name: "", zone_type: "area", floor_ref: "", indoor_outdoor: "unknown" });
const geoForm = ref({ zone_id: "", geometry_type: "polygon", wkt: "", source_id: "" });

async function load() {
  try {
    place.value = await get(`/places/${placeId}`);
    zones.value = await get(`/places/${placeId}/zones`);
    rules.value = (await get(`/places/${placeId}/rules`)) as unknown as Rule[];
    geometries.value = await get(`/places/${placeId}/geometries`);
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function createZone() {
  error.value = "";
  try {
    await post("/zones", {
      place_id: placeId,
      name: zoneForm.value.name,
      zone_type: zoneForm.value.zone_type,
      floor_ref: zoneForm.value.floor_ref || null,
      indoor_outdoor: zoneForm.value.indoor_outdoor,
    });
    zoneForm.value = { name: "", zone_type: "area", floor_ref: "", indoor_outdoor: "unknown" };
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function createGeometry() {
  error.value = "";
  try {
    await post("/geometries", {
      place_id: geoForm.value.zone_id ? null : placeId,
      zone_id: geoForm.value.zone_id || null,
      geometry_type: geoForm.value.geometry_type,
      wkt: geoForm.value.wkt,
      source_id: geoForm.value.source_id,
    });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>{{ place?.canonical_name ?? "场所详情" }}</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <p class="muted" v-if="place">
    {{ place.place_type }} · {{ place.canonical_address ?? "无地址" }}
  </p>

  <h2>区域（Zone）</h2>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>名称</th>
          <th>类型</th>
          <th>楼层</th>
          <th>室内/户外</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="z in zones" :key="z.id">
          <td>{{ z.name }}</td>
          <td>
            <span class="tag">{{ z.zone_type }}</span>
          </td>
          <td>{{ z.floor_ref ?? "—" }}</td>
          <td>{{ z.indoor_outdoor }}</td>
        </tr>
        <tr v-if="!zones.length">
          <td colspan="4" class="muted">暂无区域</td>
        </tr>
      </tbody>
    </table>
    <div class="row" style="margin-top: 12px">
      <div><label>新区域名称</label><input v-model="zoneForm.name" /></div>
      <div>
        <label for="fld-zoneform-zone-type">类型</label>
        <select v-model="zoneForm.zone_type" id="fld-zoneform-zone-type">
          <option value="area">area</option>
          <option value="floor">floor</option>
          <option value="children_area">children_area</option>
          <option value="pet_area">pet_area</option>
          <option value="lawn">lawn</option>
          <option value="road">road</option>
          <option value="supermarket">supermarket</option>
          <option value="dining_area">dining_area</option>
        </select>
      </div>
      <div>
        <label>楼层引用</label><input v-model="zoneForm.floor_ref" placeholder="如 3F / B1" />
      </div>
      <div>
        <label for="fld-zoneform-indoor-outdoor">室内/户外</label>
        <select v-model="zoneForm.indoor_outdoor" id="fld-zoneform-indoor-outdoor">
          <option value="indoor">indoor</option>
          <option value="outdoor">outdoor</option>
          <option value="semi_open">semi_open</option>
          <option value="unknown">unknown</option>
        </select>
      </div>
      <button
        class="primary"
        style="align-self: end; flex: 0"
        :disabled="!zoneForm.name"
        @click="createZone"
      >
        新增区域
      </button>
    </div>
  </div>

  <h2>规则</h2>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>对象</th>
          <th>动物</th>
          <th>动作</th>
          <th>效果</th>
          <th>状态</th>
          <th>来源</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rules" :key="r.id">
          <td class="muted">
            {{ r.zone_id ? (zones.find((z) => z.id === r.zone_id)?.name ?? "区域") : "全场" }}
          </td>
          <td>{{ r.animal_scope }}</td>
          <td>{{ r.action }}</td>
          <td>
            <span
              class="tag"
              :class="{ restricted: r.effect === 'prohibited', ok: r.effect === 'allowed' }"
              >{{ r.effect }}</span
            >
          </td>
          <td>{{ r.status }}</td>
          <td class="muted">{{ r.rule_origin }}</td>
        </tr>
        <tr v-if="!rules.length">
          <td colspan="6" class="muted">暂无规则</td>
        </tr>
      </tbody>
    </table>
  </div>

  <h2>几何数据（PostGIS）</h2>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>归属</th>
          <th>类型</th>
          <th>精度</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="g in geometries" :key="g.id">
          <td>
            {{ g.zone_id ? (zones.find((z) => z.id === g.zone_id)?.name ?? g.zone_id) : "场所" }}
          </td>
          <td>{{ g.geometry_type }}</td>
          <td>{{ g.precision }}</td>
        </tr>
        <tr v-if="!geometries.length">
          <td colspan="3" class="muted">暂无几何</td>
        </tr>
      </tbody>
    </table>
    <div class="row" style="margin-top: 12px">
      <div>
        <label for="fld-geoform-zone-id">归属区域（可空=场所）</label>
        <select v-model="geoForm.zone_id" id="fld-geoform-zone-id">
          <option value="">场所本身</option>
          <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
        </select>
      </div>
      <div>
        <label for="fld-geoform-geometry-type">几何类型</label>
        <select v-model="geoForm.geometry_type" id="fld-geoform-geometry-type">
          <option value="polygon">polygon</option>
          <option value="point">point</option>
          <option value="linestring">linestring</option>
          <option value="multipolygon">multipolygon</option>
        </select>
      </div>
      <div style="flex: 2">
        <label>WKT</label
        ><input
          v-model="geoForm.wkt"
          placeholder="POLYGON((121.47 31.23,121.48 31.23,121.48 31.24,121.47 31.23))"
        />
      </div>
      <div><label>来源 ID</label><input v-model="geoForm.source_id" /></div>
      <button
        class="primary"
        style="align-self: end; flex: 0"
        :disabled="!geoForm.wkt || !geoForm.source_id"
        @click="createGeometry"
      >
        新增几何
      </button>
    </div>
  </div>
</template>
