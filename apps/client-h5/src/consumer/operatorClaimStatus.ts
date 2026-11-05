const CLAIM_STATUS_LABELS: Record<string, string> = {
  submitted: "等待人工核验",
  verifying: "正在核验",
  approved: "认领已通过",
  rejected: "认领未通过",
  revoked: "认领已撤销",
};

export function operatorClaimStatusLabel(status: string): string {
  return CLAIM_STATUS_LABELS[status] ?? "";
}
