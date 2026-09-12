<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { COLLECTOR_TYPES, EVIDENCE_CLASSES, EXTRACTION_METHODS } from "../v05";

interface Artifact {
  id: string;
  source_id: string | null;
  source_platform: string;
  collector_type: string;
  artifact_type: string;
  source_url: string | null;
  content_hash: string | null;
  collected_at: string | null;
  publisher_type: string;
  published_at: string | null;
  captured_excerpt: string | null;
  storage_allowed: boolean;
  display_allowed: boolean;
  redistribution_allowed: boolean;
}

interface Bundle {
  id: string;
  artifact_id: string;
  source_id: string | null;
  source_platform: string;
  source_url: string | null;
  publisher_type: string;
  quoted_fragment: string | null;
  extracted_fragment: string | null;
  evidence_class: string;
  content_hash: string | null;
  extraction_method: string | null;
  derived_from_bundle_id: string | null;
  place_match_evidence: Record<string, unknown> | null;
  license_metadata: Record<string, unknown> | null;
}

const artifacts = ref<Artifact[]>([]);
const bundles = ref<Bundle[]>([]);
const error = ref("");
const info = ref("");
const busy = ref(false);
/** Bumped on every write so the artifact list reflects the new bundle count. */
const reload = ref(0);

const form = ref({
  source_id: "",
  collector_type: "OfficialWebCollector",
  artifact_type: "web_page",
  source_url: "",
  content_hash: "",
  captured_excerpt: "",
  publisher_type: "operator",
});

/** Collector → platform preview, mirrors `_platform_for_collector` on the API. */
const platformPreview = ref("official_web");

const bundleForm = ref({
  artifact_id: "",
  quoted_fragment: "",
  extracted_fragment: "",
  evidence_class: "original",
  extraction_method: "manual",
  derived_from_bundle_id: "",
});

const leadOnly = ref(false);

function onCollectorChange() {
  const found = COLLECTOR_TYPES.find((c) => c.value === form.value.collector_type);
  leadOnly.value = Boolean(found?.leadOnly);
}

async function load() {
  error.value = "";
  try {
    const [a, b] = await Promise.all([
      page<Artifact>("/admin/source-artifacts", { limit: 50 }),
      page<Bundle>("/admin/evidence-bundles", { limit: 50 }),
    ]);
    artifacts.value = a.items;
    bundles.value = b.items;
  } catch (e) {
    error.value = errText(e);
  }
}

async function createArtifact() {
  error.value = "";
  info.value = "";
  busy.value = true;
  try {
    const payload: Record<string, unknown> = {
      collector_type: form.value.collector_type,
      artifact_type: form.value.artifact_type,
      publisher_type: form.value.publisher_type,
      display_allowed: false,
      redistribution_allowed: false,
    };
    if (form.value.source_id) payload.source_id = form.value.source_id;
    if (form.value.source_url) payload.source_url = form.value.source_url;
    if (form.value.content_hash) payload.content_hash = form.value.content_hash;
    if (form.value.captured_excerpt) payload.captured_excerpt = form.value.captured_excerpt;
    const created = await post<Artifact>("/admin/source-artifacts", payload);
    info.value = `已冻结证据原件 ${created.id.slice(0, 8)}…（${created.source_platform}）`;
    bundleForm.value.artifact_id = created.id;
    reload.value++;
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = false;
  }
}

async function createBundle() {
  error.value = "";
  info.value = "";
  busy.value = true;
  try {
    const payload: Record<string, unknown> = {
      artifact_id: bundleForm.value.artifact_id,
      evidence_class: bundleForm.value.evidence_class,
    };
    if (bundleForm.value.quoted_fragment) payload.quoted_fragment = bundleForm.value.quoted_fragment;
    if (bundleForm.value.extracted_fragment) payload.extracted_fragment = bundleForm.value.extracted_fragment;
    if (bundleForm.value.extraction_method) payload.extraction_method = bundleForm.value.extraction_method;
    if (bundleForm.value.derived_from_bundle_id) payload.derived_from_bundle_id = bundleForm.value.derived_from_bundle_id;
    const created = await post<Bundle>("/admin/evidence-bundles", payload);
    info.value = `已创建证据包 ${created.id.slice(0, 8)}…（${created.evidence_class}）`;
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = false;
  }
}

onMounted(() => {
  onCollectorChange();
  void load();
});
</script>

<template>
  <h1>证据复核</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="info" class="ok-banner">{{ info }}</div>

  <p class="muted">
    证据链：<span class="mono">SourceArtifact → EvidenceBundle → Claim → Candidate</span>。
    只有原始证据（original）具独立权重；派生证据（derived）必须引用其来源证据包，否则 API 拒绝（
    <span class="mono">derived_evidence_requires_origin</span>）。
  </p>

  <div class="two-col">
    <!-- ---------------- freeze an artifact ---------------- -->
    <div class="panel">
      <h2>① 冻结证据原件</h2>
      <div class="field">
        <label>采集器</label>
        <select v-model="form.collector_type" @change="onCollectorChange">
          <option v-for="c in COLLECTOR_TYPES" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>
      <div v-if="leadOnly" class="lead-warn">
        该采集器仅产出「线索」，不携带可直接发布的内容 —— 后续必须经人工核实，不得直接发布。
      </div>
      <div class="row">
        <div class="field">
          <label>原件类型</label>
          <input v-model="form.artifact_type" placeholder="web_page / signage_photo / phone_note" />
        </div>
        <div class="field">
          <label>发布者类型</label>
          <select v-model="form.publisher_type">
            <option value="official">official（官方）</option>
            <option value="operator">operator（经营方）</option>
            <option value="third_party">third_party（第三方）</option>
            <option value="user">user（用户）</option>
            <option value="unknown">unknown（未知）</option>
          </select>
        </div>
      </div>
      <label>来源 URL</label>
      <input v-model="form.source_url" placeholder="https://…" />
      <label>来源 ID（可选，关联 Source 表）</label>
      <input v-model="form.source_id" class="mono" placeholder="uuid" />
      <label>内容哈希（可选，用于变更检测）</label>
      <input v-model="form.content_hash" class="mono" placeholder="sha256…" />
      <label>抓取摘录</label>
      <textarea v-model="form.captured_excerpt" rows="3" placeholder="页面/照片中与准入相关的原文片段" />
      <p class="hint">
        默认 <span class="mono">display_allowed=false</span>、<span class="mono">redistribution_allowed=false</span> ——
        未明确授权前不得对外展示或再分发。
      </p>
      <button class="primary" style="margin-top: 10px" :disabled="busy" @click="createArtifact">
        冻结为证据原件
      </button>
    </div>

    <!-- ---------------- create a bundle ---------------- -->
    <div class="panel">
      <h2>② 生成可归因证据包</h2>
      <label>关联证据原件</label>
      <input v-model="bundleForm.artifact_id" class="mono" placeholder="artifact uuid" />
      <div class="field" style="margin-top: 10px">
        <label>证据类别</label>
        <select v-model="bundleForm.evidence_class">
          <option v-for="c in EVIDENCE_CLASSES" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>
      <div v-if="bundleForm.evidence_class === 'derived'" class="field" style="margin-top: 10px">
        <label>引用原始证据包 ID（派生必填）</label>
        <input v-model="bundleForm.derived_from_bundle_id" class="mono" placeholder="bundle uuid" />
      </div>
      <label>引用片段</label>
      <textarea v-model="bundleForm.quoted_fragment" rows="2" placeholder="逐字引用，保持可追溯" />
      <label>抽取片段</label>
      <textarea v-model="bundleForm.extracted_fragment" rows="2" placeholder="结构化抽取结果（可改写）" />
      <div class="field" style="margin-top: 10px">
        <label>抽取方式</label>
        <select v-model="bundleForm.extraction_method">
          <option v-for="m in EXTRACTION_METHODS" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <button class="primary" style="margin-top: 10px" :disabled="busy || !bundleForm.artifact_id" @click="createBundle">
        生成证据包
      </button>
    </div>
  </div>

  <!-- ---------------- lists ---------------- -->
  <div class="panel">
    <h2>证据原件（{{ artifacts.length }}）</h2>
    <table class="compact">
      <thead>
        <tr><th>ID</th><th>平台 / 采集器</th><th>类型</th><th>URL</th><th>哈希</th><th>授权</th><th>采集时间</th></tr>
      </thead>
      <tbody>
        <tr v-for="a in artifacts" :key="a.id">
          <td class="mono">{{ shortId(a.id) }}</td>
          <td class="mono">{{ a.source_platform }}<br /><span class="muted">{{ a.collector_type }}</span></td>
          <td>{{ a.artifact_type }}</td>
          <td class="mono" style="max-width: 220px; overflow: hidden; text-overflow: ellipsis">{{ a.source_url ?? "—" }}</td>
          <td class="mono">{{ a.content_hash ?? "—" }}</td>
          <td>
            <span class="tag" :class="a.display_allowed ? 'ok' : 'unknown'">展示 {{ a.display_allowed ? "允许" : "禁止" }}</span>
            <span class="tag" :class="a.redistribution_allowed ? 'ok' : 'unknown'" style="margin-left: 4px">再分发 {{ a.redistribution_allowed ? "允许" : "禁止" }}</span>
          </td>
          <td class="muted">{{ ts(a.collected_at) }}</td>
        </tr>
        <tr v-if="!artifacts.length"><td colspan="7" class="muted">暂无证据原件</td></tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>证据包（{{ bundles.length }}）</h2>
    <table class="compact">
      <thead>
        <tr><th>ID</th><th>原件</th><th>类别</th><th>引用片段</th><th>抽取方式</th><th>来源证据包</th></tr>
      </thead>
      <tbody>
        <tr v-for="b in bundles" :key="b.id">
          <td class="mono">{{ shortId(b.id) }}</td>
          <td class="mono">{{ shortId(b.artifact_id) }}</td>
          <td><span class="tag" :class="b.evidence_class === 'original' ? 'ok' : 'warn'">{{ b.evidence_class }}</span></td>
          <td class="quote">{{ b.quoted_fragment || b.extracted_fragment || "—" }}</td>
          <td class="mono">{{ b.extraction_method ?? "—" }}</td>
          <td class="mono">{{ shortId(b.derived_from_bundle_id) }}</td>
        </tr>
        <tr v-if="!bundles.length"><td colspan="6" class="muted">暂无证据包</td></tr>
      </tbody>
    </table>
  </div>
</template>
