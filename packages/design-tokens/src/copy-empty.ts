/**
 * @petaccess/design-tokens — unified empty-state copy (M2 §26).
 *
 * One agreed wording per context, so no page invents its own empty state.
 * Every consumer page that can legitimately render nothing maps to a key here.
 */

export type EmptyContextKey =
  | "HOME"
  | "SEARCH"
  | "MAP"
  | "RULE"
  | "REALITY"
  | "STAFF"
  | "FACILITY"
  | "EVIDENCE"
  | "CONTRIBUTION_HISTORY";

export interface EmptyStateCopy {
  readonly title: string;
  readonly description: string;
  readonly primary: string;
  readonly secondary: string;
}

/** One agreed empty-state wording per context (M2 §26), so no page invents one. */
export const EMPTY_STATE_COPY: Readonly<Record<EmptyContextKey, EmptyStateCopy>> = {
  HOME: {
    title: "当前还没有已发布的场所数据",
    description: "你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。",
    primary: "探索地图",
    secondary: "贡献线索",
  },
  SEARCH: {
    title: "没有找到已收录场所",
    description: "试试其他关键词，或提交一个新的场所线索。",
    primary: "提交场所线索",
    secondary: "清除筛选",
  },
  MAP: {
    title: "地图暂无已发布场所",
    description: "当前区域还没有已发布的数据。未收录不代表场所没有规则。",
    primary: "返回首页",
    secondary: "",
  },
  RULE: {
    title: "暂无规则记录",
    description: "尚未收录该场所的规则。未收录不代表场所没有规则。",
    primary: "贡献规则线索",
    secondary: "",
  },
  REALITY: {
    title: "暂无足够现场记录",
    description: "暂无记录不代表现实中没有动物。",
    primary: "贡献现场记录",
    secondary: "",
  },
  STAFF: {
    title: "暂无工作人员响应记录",
    description: "今天还没有来自管理方的现场响应记录。",
    primary: "",
    secondary: "",
  },
  FACILITY: {
    title: "暂无设施信息",
    description: "该场所尚未收录设施信息。",
    primary: "",
    secondary: "",
  },
  EVIDENCE: {
    title: "暂无可见证据",
    description: "该场所还没有公开可见的依据条目。",
    primary: "",
    secondary: "",
  },
  CONTRIBUTION_HISTORY: {
    title: "还没有贡献记录",
    description: "你提交的现场记录与规则线索会出现在这里。",
    primary: "去贡献",
    secondary: "",
  },
};