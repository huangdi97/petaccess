/**
 * Consumer-facing source identity policy.
 *
 * Institution/government/operator issuers may be displayed when present.
 * Ordinary-user provenance is intentionally de-identified even after the
 * underlying fact or rule has been reviewed for publication.
 */
const SOURCE_FALLBACK_LABELS: Record<string, string> = {
  statute_or_regulation: "法规来源",
  government_service: "政府来源",
  official_operator_policy: "管理方来源",
  onsite_signage: "现场标识",
  certified_verifier: "认证核验方",
  ordinary_user: "普通用户贡献（身份不公开）",
  external_web_reference: "外部网页来源",
  imported_dataset: "导入数据来源",
};

export function publicSourceIssuer(
  sourceType: string | null | undefined,
  issuer: string | null | undefined,
): string {
  if (sourceType === "ordinary_user") return "普通用户贡献（身份不公开）";
  const value = issuer?.trim();
  return value || SOURCE_FALLBACK_LABELS[sourceType ?? ""] || "来源待补充";
}
