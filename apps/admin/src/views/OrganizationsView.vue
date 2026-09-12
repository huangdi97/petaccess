<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { ANIMAL_SCOPES, EFFECTS, RULE_LAYERS } from "../v05";

interface Organization {
  id: string;
  name: string;
  kind: string;
  status: string | null;
  created_at: string | null;
}

interface TemplateRule {
  animal_scope: string;
  action: string;
  effect: string;
  rule_layer: string;
  notes: string | null;
}

interface Template {
  id: string;
  organization_id: string;
  name: string;
  venue_scope: string | null;
  status: string;
  rule_count: number;
  rules: TemplateRule[];
  created_at: string | null;
}

interface Binding {
  id: string;
  place_id: string;
  template_id: string | null;
  source_id: string | null;
  is_active: boolean;
  overrides: unknown;
  created_at: string | null;
}

interface DraftRule {
  animal_scope: string;
  action: string;
  effect: string;
  notes: string;
}

const orgs = ref<Organization[]>([]);
const templates = ref<Template[]>([]);
const bindings = ref<Binding[]>([]);
const error = ref("");
const info = ref("");
const busy = ref("");

const orgForm = ref({ name: "", kind: "brand" });

const tplForm = ref({
  organization_id: "",
  name: "",
  venue_scope: "",
  rules: [{ animal_scope: "dog", action: "enter", effect: "prohibited", notes: "" }] as DraftRule[],
});

const bindForm = ref({ place_id: "", template_id: "", source_id: "", overridesJson: "[]" });

function addRule() {
  tplForm.value.rules.push({ animal_scope: "dog", action: "enter", effect: "prohibited", notes: "" });
}
function removeRule(i: number) {
  tplForm.value.rules.splice(i, 1);
}

async function load() {
  error.value = "";
  try {
    const [o, t, b] = await Promise.all([
      page<Organization>("/admin/organizations", { limit: 50 }),
      page<Template>("/admin/policy-templates", { limit: 50 }),
      page<Binding>("/admin/place-policy-bindings", { limit: 50 }),
    ]);
    orgs.value = o.items;
    templates.value = t.items;
    bindings.value = b.items;
  } catch (e) {
    error.value = errText(e);
  }
}

async function createOrg() {
  error.value = "";
  info.value = "";
  busy.value = "org";
  try {
    const created = await post<{ id: string; name: string }>("/admin/organizations", {
      name: orgForm.value.name,
      kind: orgForm.value.kind,
    });
    info.value = `已创建组织 ${created.name}（${created.id.slice(0, 8)}…）`;
    tplForm.value.organization_id = created.id;
    orgForm.value.name = "";
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

async function createTemplate() {
  error.value = "";
  info.value = "";
  busy.value = "tpl";
  try {
    const created = await post<{ id: string; name: string; rules: number }>("/admin/policy-templates", {
      organization_id: tplForm.value.organization_id,
      name: tplForm.value.name,
      venue_scope: tplForm.value.venue_scope || null,
      rules: tplForm.value.rules.map((r) => ({
        animal_scope: r.animal_scope,
        action: r.action,
        effect: r.effect,
        conditions: null,
        notes: r.notes || null,
      })),
    });
    info.value = `已创建政策模板「${created.name}」，含 ${created.rules} 条规则`;
    bindForm.value.template_id = created.id;
    tplForm.value.name = "";
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

async function createBinding() {
  error.value = "";
  info.value = "";
  let overrides: unknown = null;
  try {
    overrides = bindForm.value.overridesJson ? JSON.parse(bindForm.value.overridesJson) : null;
  } catch {
    error.value = "覆盖项 JSON 格式非法";
    return;
  }
  busy.value = "bind";
  try {
    const payload: Record<string, unknown> = { place_id: bindForm.value.place_id, overrides };
    if (bindForm.value.template_id) payload.template_id = bindForm.value.template_id;
    if (bindForm.value.source_id) payload.source_id = bindForm.value.source_id;
    const created = await post<{ id: string; place_id: string }>("/admin/place-policy-bindings", payload);
    info.value = `已绑定场所 ${created.place_id.slice(0, 8)}…（旧绑定自动失活，历史保留）`;
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
  <h1>组织 · 政策模板 · 场所覆盖</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="info" class="ok-banner">{{ info }}</div>

  <p class="muted">
    解析优先级：法规 → 监管指引 → 组织政策模板 → 场所覆盖 → 分区覆盖 → 临时/活动政策。
    模板规则层固定为 <span class="mono">OPERATOR_POLICY</span>，不得覆盖法规层；
    覆盖项与继承项<strong>并存</strong>，由解析器解释优先级，而非相互覆盖。
  </p>

  <div class="two-col">
    <div class="panel">
      <h2>① 新建组织</h2>
      <label>名称</label>
      <input v-model="orgForm.name" placeholder="例如：某某连锁咖啡" />
      <div class="field" style="margin-top: 10px">
        <label>类型</label>
        <select v-model="orgForm.kind">
          <option value="brand">brand（品牌）</option>
          <option value="chain">chain（连锁）</option>
          <option value="operator">operator（经营方）</option>
          <option value="government">government（政府）</option>
        </select>
      </div>
      <button class="primary" style="margin-top: 10px" :disabled="busy === 'org' || !orgForm.name" @click="createOrg">
        创建组织
      </button>
      <p class="hint">{{ RULE_LAYERS.map((l) => `${l.value}=${l.label}`).join(" / ") }}</p>
    </div>

    <div class="panel">
      <h2>③ 绑定到场所</h2>
      <label>场所 ID</label>
      <input v-model="bindForm.place_id" class="mono" placeholder="place uuid" />
      <label>模板 ID</label>
      <input v-model="bindForm.template_id" class="mono" placeholder="template uuid" />
      <label>来源 ID（可选）</label>
      <input v-model="bindForm.source_id" class="mono" placeholder="source uuid" />
      <label>覆盖项（JSON 数组）</label>
      <textarea v-model="bindForm.overridesJson" rows="3" class="mono" placeholder='[{"animal_scope":"dog","effect":"conditional"}]' />
      <button class="primary" style="margin-top: 10px" :disabled="busy === 'bind' || !bindForm.place_id" @click="createBinding">
        绑定并覆盖
      </button>
    </div>
  </div>

  <div class="panel">
    <h2>② 政策模板</h2>
    <div class="row">
      <div class="field">
        <label>所属组织</label>
        <select v-model="tplForm.organization_id">
          <option value="">— 选择组织 —</option>
          <option v-for="o in orgs" :key="o.id" :value="o.id">{{ o.name }}（{{ shortId(o.id) }}）</option>
        </select>
      </div>
      <div class="field">
        <label>模板名称</label>
        <input v-model="tplForm.name" placeholder="例如：标准门店政策 v2" />
      </div>
      <div class="field">
        <label>适用场馆范围</label>
        <input v-model="tplForm.venue_scope" placeholder="例如：indoor / outdoor" />
      </div>
    </div>

    <h2 style="margin-top: 16px">模板规则</h2>
    <table class="compact">
      <thead><tr><th>动物</th><th>动作</th><th>效果</th><th>说明</th><th></th></tr></thead>
      <tbody>
        <tr v-for="(r, i) in tplForm.rules" :key="i">
          <td>
            <select v-model="r.animal_scope">
              <option v-for="a in ANIMAL_SCOPES" :key="a" :value="a">{{ a }}</option>
            </select>
          </td>
          <td><input v-model="r.action" placeholder="enter" /></td>
          <td>
            <select v-model="r.effect">
              <option v-for="e in EFFECTS" :key="e" :value="e">{{ e }}</option>
            </select>
          </td>
          <td><input v-model="r.notes" placeholder="备注" /></td>
          <td><button class="danger" @click="removeRule(i)">删除</button></td>
        </tr>
      </tbody>
    </table>
    <div class="actions" style="margin-top: 10px">
      <button @click="addRule">+ 增加规则</button>
      <button class="primary" :disabled="busy === 'tpl' || !tplForm.organization_id || !tplForm.name" @click="createTemplate">
        创建模板
      </button>
    </div>
  </div>

  <div class="panel">
    <h2>已建组织（{{ orgs.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>名称</th><th>类型</th><th>创建时间</th></tr></thead>
      <tbody>
        <tr v-for="o in orgs" :key="o.id">
          <td class="mono">{{ shortId(o.id) }}</td>
          <td>{{ o.name }}</td>
          <td><span class="tag unknown">{{ o.kind }}</span></td>
          <td class="muted">{{ ts(o.created_at) }}</td>
        </tr>
        <tr v-if="!orgs.length"><td colspan="4" class="muted">暂无组织</td></tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>已建模板（{{ templates.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>名称</th><th>组织</th><th>场馆范围</th><th>规则</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="t in templates" :key="t.id">
          <td class="mono">{{ shortId(t.id) }}</td>
          <td>{{ t.name }}</td>
          <td class="mono">{{ shortId(t.organization_id) }}</td>
          <td>{{ t.venue_scope ?? "—" }}</td>
          <td>
            <span class="mono">{{ t.rule_count }} 条</span>
            <div v-for="(r, i) in t.rules" :key="i" class="hint">
              {{ r.animal_scope }} · {{ r.action }} · <strong>{{ r.effect }}</strong>
            </div>
          </td>
          <td><span class="tag unknown">{{ t.status }}</span></td>
        </tr>
        <tr v-if="!templates.length"><td colspan="6" class="muted">暂无模板</td></tr>
      </tbody>
    </table>
  </div>

  <div class="panel">
    <h2>场所绑定（{{ bindings.length }}）</h2>
    <table class="compact">
      <thead><tr><th>ID</th><th>场所</th><th>模板</th><th>来源</th><th>状态</th><th>覆盖项</th></tr></thead>
      <tbody>
        <tr v-for="b in bindings" :key="b.id">
          <td class="mono">{{ shortId(b.id) }}</td>
          <td class="mono">{{ shortId(b.place_id) }}</td>
          <td class="mono">{{ shortId(b.template_id) }}</td>
          <td class="mono">{{ shortId(b.source_id) }}</td>
          <td><span class="tag" :class="b.is_active ? 'ok' : 'unknown'">{{ b.is_active ? "生效中" : "已失活" }}</span></td>
          <td class="mono hint">{{ b.overrides ? JSON.stringify(b.overrides) : "—" }}</td>
        </tr>
        <tr v-if="!bindings.length"><td colspan="6" class="muted">暂无绑定</td></tr>
      </tbody>
    </table>
  </div>
</template>
