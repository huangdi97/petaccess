"""Correct a derived, non-authoritative field and a stale sidecar (R2-FINAL).

Scope of this correction (deliberately narrow)
----------------------------------------------

The first-party evidence chain for 和平饭店 is sound — its ``content_hash``
reproduces from the stored excerpt and the excerpt is verbatim. Two *derived*
places, however, still carried an earlier paraphrase of the operator wording:

  * ``rule_candidate.raw_text`` of ``fp-sd-op-firstparty`` — extraction working
    text, NOT the quote of record (that is ``evidence_bundle.quoted_fragment``);
  * ``docs/reality_audit/fp_sd_op_firstparty.json`` — display sidecar.

Neither is evidence, so neither should be frozen; but if they disagree with the
bundle quote a reviewer cannot tell which one to trust, which is exactly the
ambiguity this project exists to remove. Both are therefore aligned to the
verbatim wording, and the row-level change is recorded in ``audit_log``.

Nothing published or signed is touched; no source/artifact/bundle is modified.

Usage: python scripts/correct_fp_sd_op_rawtext.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.types.json import Json

REPO = Path(__file__).resolve().parents[1]
DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
SIDECAR = REPO / "docs" / "reality_audit" / "fp_sd_op_firstparty.json"

CANDIDATE_ID = "0de7771a-d461-4f86-8190-dac0604b9970"

QUOTE_ZH_HEAD = "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
QUOTE_ZH_TAIL = "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
QUOTE_ZH = QUOTE_ZH_HEAD + QUOTE_ZH_TAIL
QUOTE_EN = (
    "Fairmont Peace Hotel does not allow pets. Seeing-eye dogs are always welcome "
    "and exempt of charges and restrictions."
)
NEW_RAW_TEXT = f"{QUOTE_ZH} / {QUOTE_EN}"
NEW_HASH = hashlib.sha256(QUOTE_ZH.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    report: dict = {"apply": bool(args.apply), "candidate_id": CANDIDATE_ID}
    sidecar = json.loads(SIDECAR.read_text(encoding="utf-8"))

    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute("select raw_text from rule_candidate where id=%s", (CANDIDATE_ID,))
        row = cur.fetchone()
        if row is None:
            raise SystemExit("候选不存在：" + CANDIDATE_ID)
        report["before_raw_text"] = row[0]
        report["after_raw_text"] = NEW_RAW_TEXT
        report["raw_text_already_correct"] = row[0] == NEW_RAW_TEXT

        report["before_sidecar_quote"] = sidecar.get("quote_zh")
        report["before_sidecar_hash"] = sidecar.get("content_hash")
        report["after_content_hash"] = NEW_HASH

        if not args.apply:
            print(json.dumps({"dry_run": True, **report}, ensure_ascii=False, indent=2))
            return 0

        if row[0] != NEW_RAW_TEXT:
            cur.execute(
                "update rule_candidate set raw_text=%s where id=%s",
                (NEW_RAW_TEXT, CANDIDATE_ID),
            )
            cur.execute(
                "insert into audit_log (id, actor_user_id, actor_role, action, target_type,"
                " target_id, before_state, after_state, created_at)"
                " values (%s,%s,%s,%s,%s,%s,%s,%s,now())",
                (
                    str(uuid.uuid4()),
                    None,
                    "agent:quote_alignment",
                    "candidate.correct_raw_text",
                    "rule_candidate",
                    CANDIDATE_ID,
                    Json({"raw_text": row[0]}),
                    Json(
                        {
                            "raw_text": NEW_RAW_TEXT,
                            "reason": "align derived extraction text with the verbatim "
                            "source excerpt frozen in evidence_bundle.quoted_fragment",
                        }
                    ),
                ),
            )
            report["raw_text_updated"] = True
        else:
            report["raw_text_updated"] = False
        conn.commit()

    sidecar["quote_zh"] = QUOTE_ZH
    sidecar["content_hash"] = NEW_HASH
    sidecar["hash_formula"] = "sha256(captured_excerpt)"
    sidecar["note"] = (
        "一手来源（fairmont.com）自 2026-09-13 即为该 place 的证据锚点；"
        "本行只记录新建的、按来源原话建模的候选（guide_dog / exact）。"
        "旧行 fp-sd-op 未被改写其证据，仅因建模为粗粒度 service_dog 而建议 REJECT。"
    )
    SIDECAR.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report["sidecar_written"] = str(SIDECAR)
    print(json.dumps({"applied": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
