"""Remove duplicate Wave02 SourceMonitors (keep oldest per source_id).

Why: 和平公园 and 昆山公园 的 `ensure_source` 按 issuer+URL 去重到了同一行
source（ee605132…），但 ingest 为每个 place 各建了一个 SourceMonitor，同一
source 出现 2 条 monitor —— 生产完整性 DUPLICATE_MONITOR 暴露此问题。

处置（沿用 expansion_w01_cleanup_duplicates.py 的规则）：per source_id 保留
最早创建的一条，删除其余。仅触碰 expansion_run_id=EXP-R1-W02-20260919 的
source_monitor 行；计划产物写入 artifacts/expansion_w02/。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_session_factory  # noqa: E402

RUN_ID = "EXP-R1-W02-20260919"
ART_DIR = REPO / "artifacts" / "expansion_w02"
PLAN = ART_DIR / "wave02_monitor_dedup_plan.json"
EXEC = ART_DIR / "wave02_monitor_dedup_execute.json"


def find_dupes(session: Session) -> list[dict]:
    rows = session.execute(
        text(
            "select id, source_id, url, place_id, created_at "
            "from source_monitor where expansion_run_id = :run order by created_at, id"
        ),
        {"run": RUN_ID},
    ).fetchall()
    by_src: dict[str, list] = {}
    for r in rows:
        by_src.setdefault(str(r[1]), []).append(
            {
                "id": str(r[0]),
                "source_id": str(r[1]),
                "url": r[2],
                "place_id": str(r[3]) if r[3] else None,
                "created_at": str(r[4]),
            }
        )
    dupes = []
    for mons in by_src.values():
        if len(mons) > 1:
            keep, *rest = mons
            for m in rest:
                dupes.append({"keep": keep, "remove": m})
    return dupes


def main() -> int:
    ap = argparse.ArgumentParser(description="Wave02 duplicate monitor removal")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    session = get_session_factory()()
    dupes = find_dupes(session)
    print(f"DUPLICATE_GROUPS = {len(dupes)}")
    for d in dupes:
        print(f"  keep   {d['keep']['id']} (place {d['keep']['place_id']})")
        print(f"  remove {d['remove']['id']} (place {d['remove']['place_id']})")

    doc = {
        "operation": "wave02_monitor_dedup",
        "run_id": RUN_ID,
        "at": datetime.now(UTC).isoformat(),
        "reason": "same source deduped by issuer+url; one monitor per source is enough",
        "groups": dupes,
    }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", PLAN)

    if args.execute:
        ids = [d["remove"]["id"] for d in dupes]
        session.execute(
            text("delete from source_monitor where id = any(:ids) and expansion_run_id = :run"),
            {"ids": ids, "run": RUN_ID},
        )
        session.commit()
        print(f"REMOVED {len(ids)} duplicate monitors")
        after = find_dupes(session)
        EXEC.write_text(
            json.dumps(
                {
                    "deleted": ids,
                    "residual_duplicate_groups": len(after),
                    "at": datetime.now(UTC).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("WROTE", EXEC)
    session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
