"""Read-only probe for the Wave 01 pre-real-publish semantic bridge.

Dumps, per signed Wave-01 candidate, the fields the bridge has to reason about:
declared scope/normalisation, the condition keys actually stored, and the source
text the normalisation claims to be faithful to. Never writes.
"""

from __future__ import annotations

import subprocess
import sys

RUN_ID = "EXP-R1-W01-20260918"

SQL = f"""
SELECT rc.id, p.canonical_name, rc.animal_scope, rc.subject_scope_normalized,
       rc.normalization_type, rc.effect, rc.rule_layer, rc.action, rc.source_scope_exact,
       rc.proposed_conditions::text, rc.holder_scope, rc.mandatory_level,
       rc.evidence_bundle_id, rc.source_id, rc.review_status
FROM rule_candidate rc
LEFT JOIN place p ON p.id = rc.place_id
WHERE rc.expansion_run_id = '{RUN_ID}'
ORDER BY p.canonical_name, rc.animal_scope
"""


def psql(sql: str) -> list[list[str]]:
    out = subprocess.run(
        [
            "docker",
            "exec",
            "petaccess-db-1",
            "psql",
            "-U",
            "petaccess",
            "-d",
            "petaccess",
            "-A",
            "-t",
            "-F",
            "\x1f",
            "-c",
            sql,
        ],
        capture_output=True,
    )
    text = out.stdout.decode("utf-8", errors="replace")
    if out.returncode != 0:
        sys.stderr.write(out.stderr.decode("utf-8", errors="replace"))
    return [ln.split("\x1f") for ln in text.splitlines() if ln.strip()]


def main() -> None:
    rows = psql(SQL)
    print(f"candidates={len(rows)}")
    for r in rows:
        (
            cid,
            name,
            ascope,
            snorm,
            ntype,
            eff,
            layer,
            action,
            sexact,
            conds,
            holder,
            mand,
            bundle,
            source,
            status,
        ) = r
        print("=" * 100)
        print(f"cid={cid[:8]}  place={name}")
        print(f"  animal_scope={ascope} normalized={snorm} norm_type={ntype}")
        print(f"  effect={eff} layer={layer} action={action} mandatory={mand} holder={holder}")
        print(f"  source_scope_exact={sexact!r}  status={status}")
        print(f"  conditions={conds}")
        print(f"  bundle={bundle} source={source}")

    print("\n\n######## EVIDENCE ########")
    bundles = sorted({r[12] for r in rows if r[12]})
    for b in bundles:
        q = f"""
        SELECT eb.id, sa.source_url, sa.evidence_strength, sa.collector_type, sa.storage_allowed,
               sa.collected_at, eb.quoted_fragment, eb.review_log::text, sa.captured_excerpt
        FROM evidence_bundle eb JOIN source_artifact sa ON sa.id = eb.artifact_id
        WHERE eb.id = '{b}'
        """
        for e in psql(q):
            (bid, uri, strength, cap, storage, collected, frag, log, excerpt) = e
            print("=" * 100)
            print(f"bundle={bid[:8]} strength={strength} collector={cap} storage={storage}")
            print(f"  collected={collected}")
            print(f"  uri={uri}")
            print(f"  review_log={log[:300] if log else None}")
            print(f"  fragment={(frag or '')[:700]!r}")
            print(f"  excerpt={(excerpt or '')[:700]!r}")


if __name__ == "__main__":
    main()
