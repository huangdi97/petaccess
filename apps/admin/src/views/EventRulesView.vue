<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { ANIMAL_SCOPES, EFFECTS } from "../v05";

interface EventPolicy {
  id: string;
  place_id: string;
  zone_id: string | null;
  name: string;
  animal_scope: string;
  action: string;
  effect: string;
  time_window: string | null;
  effective_from: string | null;
  effective_to: string | null;
  is_effective_now: boolean;
  source_id: string;
}

interface DataLicense {
  id: string;
  source_id: string;
  license_name: string | null;
  display_allowed: boolean;
  storage_allowed: boolean;
  redistribution_allowed: boolean;
  commercial_use_allowed: boolean;
  attribution_required: boolean;
}

const events = ref<EventPolicy[]>([]);
const licenses = ref<DataLicense[]>([]);
const error = ref("");
const info = ref("");
const busy = ref("");

const eventForm = ref({
  place_id: "",
  zone_id: "",
  name: "",
  animal_scope: "dog",
  action: "enter",
  effect: "prohibited",
  time_window: "",
  effective_from: "",
  effective_to: "",
  source_id: "",
});

const licenseForm = ref({
  source_id: "",
  license_name: "",
  display_allowed: true,
  storage_allowed: true,
  redistribution_allowed: false,
  commercial_use_allowed: false,
  attribution_required: true,
});

async function load() {
  error.value = "";
  try {
    const [ev, lic] = await Promise.all([
      page<EventPolicy>("/admin/event-policies", { limit: 50 }),
      page<DataLicense>("/admin/data-licenses", { limit: 50 }),
    ]);
    events.value = ev.items;
    licenses.value = lic.items;
  } catch (e) {
    error.value = errText(e);
  }
}

/** Convert a `datetime-local` value into an ISO string the API accepts. */
function toIso(local: string): string | null {
  if (!local) return null;
  const d = new Date(local);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

async function createEvent() {
  error.value = "";
  info.value = "";
  const from = toIso(eventForm.value.effective_from);
  const to = toIso(eventForm.value.effective_to);
  if (!from || !to) {
    error.value = "生效起止时间必填";
    return;
  }
  busy.value = "event";
  try {
    const created = await post<{ id: string }>("/admin/event-policies", {
      place_id: eventForm.value.place_id,
      zone_id: eventForm.value.zone_id || null,
      name: eventForm.value.name,
      animal_scope: eventForm.value.animal_scope,
      action: eventForm.value.action,
      effect: eventForm.value.effect,
      time_window: eventForm.value.time_window || null,
      effective_from: from,
      effective_to: to,
      source_id: eventForm.value.source_id,
    });
    info.value = `已创建活动/临时政策 ${created.id.slice(0, 8)}…（层 TEMPORARY_POLICY）`;
    eventForm.value.name = "";
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

async function createLicense() {
  error.value = "";
  info.value = "";
  busy.value = "license";
  try {
    const created = await post<{ id: string }>("/admin/data-licenses", {
      source_id: licenseForm.value.source_id,
      license_name: licenseForm.value.license_name || null,
      display_allowed: licenseForm.value.display_allowed,
      storage_allowed: licenseForm.value.storage_allowed,
      redistribution_allowed: licenseForm.value.redistribution_allowed,
      commercial_use_allowed: licenseForm.value.commercial_use_allowed,
      attribution_required: licenseForm.value.attribution_required,
    });
    info.value = `已登记数据许可 ${created.id.slice(0, 8)}…`;
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
  <h1>活动政策 · 数据许可</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="info" class="ok-banner">{{ info }}</div>

  <div class="panel">
    <h2>① 活动 / 临时政策（EventPolicy）</h2>
    <p class="muted">
      例如「展会期间禁止携宠」「雨季场地关闭」。统一归入
      <span class="mono">TEMPORARY_POLICY</span> 层，
      仅在生效时间窗内参与解析，过期自动失效而不删除。
    </p>
    <div class="row">
      <div class="field">
        <label>场所 ID</label
        ><input v-model="eventForm.place_id" class="mono" placeholder="place uuid" />
      </div>
      <div class="field">
        <label>分区 ID（可选）</label
        ><input v-model="eventForm.zone_id" class="mono" placeholder="zone uuid" />
      </div>
      <div class="field">
        <label>名称</label><input v-model="eventForm.name" placeholder="春季宠物展管控" />
      </div>
    </div>
    <div class="row">
      <div class="field">
        <label>适用动物</label>
        <select v-model="eventForm.animal_scope">
          <option v-for="a in ANIMAL_SCOPES" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="field">
        <label>动作</label><input v-model="eventForm.action" placeholder="enter" />
      </div>
      <div class="field">
        <label>效果</label>
        <select v-model="eventForm.effect">
          <option v-for="e in EFFECTS" :key="e" :value="e">{{ e }}</option>
        </select>
      </div>
      <div class="field">
        <label>时间窗（可选）</label
        ><input v-model="eventForm.time_window" placeholder="10:00-18:00" />
      </div>
    </div>
    <div class="row">
      <div class="field">
        <label>生效开始</label><input v-model="eventForm.effective_from" type="datetime-local" />
      </div>
      <div class="field">
        <label>生效结束</label><input v-model="eventForm.effective_to" type="datetime-local" />
      </div>
      <div class="field">
        <label>来源 ID</label
        ><input v-model="eventForm.source_id" class="mono" placeholder="source uuid" />
      </div>
    </div>
    <button
      class="primary"
      style="margin-top: 10px"
      :disabled="busy === 'event' || !eventForm.place_id || !eventForm.name || !eventForm.source_id"
      @click="createEvent"
    >
      创建活动政策
    </button>
  </div>

  <div class="panel">
    <h2>② 数据许可（DataLicense）</h2>
    <p class="muted">
      每个来源的使用边界：能否对外展示、能否存储、能否再分发、能否商用、是否需署名。
      证据包会继承来源的许可元数据。
    </p>
    <div class="row">
      <div class="field">
        <label>来源 ID</label
        ><input v-model="licenseForm.source_id" class="mono" placeholder="source uuid" />
      </div>
      <div class="field">
        <label>许可名称（可选）</label
        ><input v-model="licenseForm.license_name" placeholder="CC BY-NC / 内部授权" />
      </div>
    </div>
    <table class="compact" style="margin-top: 12px">
      <thead>
        <tr>
          <th>权限</th>
          <th>取值</th>
          <th>说明</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>对外展示</td>
          <td>
            <input v-model="licenseForm.display_allowed" type="checkbox" style="width: auto" />
          </td>
          <td class="muted">允许在用户端展示来源内容</td>
        </tr>
        <tr>
          <td>存储留存</td>
          <td>
            <input v-model="licenseForm.storage_allowed" type="checkbox" style="width: auto" />
          </td>
          <td class="muted">允许在本平台长期留存</td>
        </tr>
        <tr>
          <td>再分发</td>
          <td>
            <input
              v-model="licenseForm.redistribution_allowed"
              type="checkbox"
              style="width: auto"
            />
          </td>
          <td class="muted">允许向第三方再分发</td>
        </tr>
        <tr>
          <td>商用</td>
          <td>
            <input
              v-model="licenseForm.commercial_use_allowed"
              type="checkbox"
              style="width: auto"
            />
          </td>
          <td class="muted">允许用于商业用途</td>
        </tr>
        <tr>
          <td>需署名</td>
          <td>
            <input v-model="licenseForm.attribution_required" type="checkbox" style="width: auto" />
          </td>
          <td class="muted">展示时必须标注来源</td>
        </tr>
      </tbody>
    </table>
    <button
      class="primary"
      style="margin-top: 10px"
      :disabled="busy === 'license' || !licenseForm.source_id"
      @click="createLicense"
    >
      登记数据许可
    </button>
  </div>

  <div class="panel">
    <h2>活动政策列表（{{ events.length }}）</h2>
    <table class="compact">
      <thead>
        <tr>
          <th>ID</th>
          <th>场所</th>
          <th>名称</th>
          <th>动物 / 动作 / 效果</th>
          <th>生效窗口</th>
          <th>当前生效</th>
          <th>来源</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in events" :key="ev.id">
          <td class="mono">{{ shortId(ev.id) }}</td>
          <td class="mono">{{ shortId(ev.place_id) }}</td>
          <td>{{ ev.name }}</td>
          <td>
            {{ ev.animal_scope }} · {{ ev.action }} · <strong>{{ ev.effect }}</strong>
          </td>
          <td class="muted">{{ ts(ev.effective_from) }} → {{ ts(ev.effective_to) }}</td>
          <td>
            <span class="tag" :class="ev.is_effective_now ? 'ok' : 'unknown'">{{
              ev.is_effective_now ? "生效中" : "未生效"
            }}</span>
          </td>
          <td class="mono">{{ shortId(ev.source_id) }}</td>
        </tr>
        <tr v-if="!events.length">
          <td colspan="7" class="muted">暂无活动政策</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>数据许可列表（{{ licenses.length }}）</h2>
    <table class="compact">
      <thead>
        <tr>
          <th>ID</th>
          <th>来源</th>
          <th>许可名称</th>
          <th>展示</th>
          <th>存储</th>
          <th>再分发</th>
          <th>商用</th>
          <th>署名</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="l in licenses" :key="l.id">
          <td class="mono">{{ shortId(l.id) }}</td>
          <td class="mono">{{ shortId(l.source_id) }}</td>
          <td>{{ l.license_name ?? "—" }}</td>
          <td>
            <span class="tag" :class="l.display_allowed ? 'ok' : 'restricted'">{{
              l.display_allowed ? "允许" : "禁止"
            }}</span>
          </td>
          <td>
            <span class="tag" :class="l.storage_allowed ? 'ok' : 'restricted'">{{
              l.storage_allowed ? "允许" : "禁止"
            }}</span>
          </td>
          <td>
            <span class="tag" :class="l.redistribution_allowed ? 'ok' : 'restricted'">{{
              l.redistribution_allowed ? "允许" : "禁止"
            }}</span>
          </td>
          <td>
            <span class="tag" :class="l.commercial_use_allowed ? 'ok' : 'restricted'">{{
              l.commercial_use_allowed ? "允许" : "禁止"
            }}</span>
          </td>
          <td>
            <span class="tag" :class="l.attribution_required ? 'warn' : 'unknown'">{{
              l.attribution_required ? "需署名" : "免署名"
            }}</span>
          </td>
        </tr>
        <tr v-if="!licenses.length">
          <td colspan="8" class="muted">暂无数据许可</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
