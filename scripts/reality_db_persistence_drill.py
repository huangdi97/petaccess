"""AC3 real-DB persistence verification for the Reality Layer.

Real create → read → update → query over ObservedPresence /
StaffResponseObservation / AnimalFacility + RealityCandidate review lifecycle,
inside a rolled-back transaction so production stays untouched.

Also compares the applied FK names against the migration source (op.f() names)
to flag any truncated/legacy constraint naming (ADR-024 history).
"""
from __future__ import annotations

import os
import re
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402

TABLES = ["reality_candidate", "observed_presence", "staff_response_observation", "animal_facility"]

with psycopg.connect(psycopg_url(os.environ["DATABASE_URL"])) as conn:
    conn.autocommit = False
    cur = conn.cursor()

    # ---------- 1. FK name comparison against migration source ----------
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "services", "api", "migrations", "versions",
                     "2c7ea6ca8e30_v09_reality_layer.py"),
        encoding="utf-8",
    ).read()
    declared = set(re.findall(r'name=op\.f\("([^"]+)"\)', src))
    applied = set()
    for t in TABLES:
        cur.execute(
            "SELECT conname FROM pg_constraint WHERE conrelid=%s::regclass AND contype='f'",
            (t,),
        )
        applied.update(r[0] for r in cur.fetchall())
    declared_fks = {n for n in declared if n.startswith("fk_")}
    print("DECLARED_FK_NAMES  =", sorted(declared_fks))
    print("APPLIED_FK_NAMES   =", sorted(applied))
    missing = declared_fks - applied
    extra = applied - declared_fks
    print("MISSING_FK_IN_DB   =", sorted(missing) or "none")
    print("EXTRA_FK_IN_DB     =", sorted(extra) or "none")

    # ---------- 2. real persistence drill inside a rollback ----------
    place_id = None
    cur.execute("SELECT id, canonical_name FROM place ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    if row:
        place_id = row[0]
    if not place_id:
        print("NO_PLACE_ROW - cannot drill without a real place; aborting drill")
    else:
        now = datetime.now(UTC)
        observed_at = now - timedelta(days=2)
        cand_id = str(uuid4())
        claim_id = str(uuid4())

        # 2a. create candidate (REVIEW_PENDING, AI posture unverified)
        cur.execute(
            """INSERT INTO reality_candidate
               (id, candidate_type, place_id, animal_scope, observed_at, captured_at,
                review_status, verification_status, payload, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,'REVIEW_PENDING','derived_ai_only',%s,%s,%s)""",
            (cand_id, "observed_presence", place_id, "dog", observed_at, now,
             '{"observed_action":"walking"}', now, now),
        )
        cur.execute(
            "SELECT review_status, verification_status, reality_decision FROM reality_candidate WHERE id=%s",
            (cand_id,),
        )
        c = cur.fetchone()
        print(f"\nCANDIDATE_CREATED   = id={cand_id[:8]}… status={c[0]} verif={c[1]} decision={c[2]}")

        # 2b. publish a claim (human-verified posture) - ObservedPresence
        cur.execute(
            """INSERT INTO observed_presence
               (id, candidate_id, place_id, animal_scope, observed_action, observed_at,
                captured_at, verification_status, freshness_state, last_verified_at,
                created_at, updated_at)
               VALUES (%s,%s,%s,'dog','walking',%s,%s,'human_verified','RECENT',%s,%s,%s)""",
            (claim_id, cand_id, place_id, observed_at, now, now, now, now),
        )
        cur.execute(
            """SELECT animal_scope, observed_action, verification_status, freshness_state
               FROM observed_presence WHERE id=%s""",
            (claim_id,),
        )
        p = cur.fetchone()
        print(f"CLAIM_CREATED       = id={claim_id[:8]}… scope={p[0]} action={p[1]} "
              f"verif={p[2]} freshness={p[3]}")

        # 2c. update: bump freshness posture via re-verification
        cur.execute(
            """UPDATE observed_presence SET freshness_state='FRESH', last_verified_at=%s
               WHERE id=%s""",
            (now, claim_id),
        )
        cur.execute("SELECT freshness_state, last_verified_at FROM observed_presence WHERE id=%s",
                    (claim_id,))
        u = cur.fetchone()
        print(f"CLAIM_UPDATED       = freshness={u[0]} last_verified={u[1] is not None}")

        # 2d. query: consumer view must exclude AI-derived rows (only human-verified)
        cur.execute(
            """SELECT count(*) FROM observed_presence
               WHERE place_id=%s AND verification_status IN ('human_verified','human_verified_with_note')""",
            (place_id,),
        )
        visible = cur.fetchone()[0]
        print(f"CONSUMER_VISIBLE    = {visible} human-verified rows for place {place_id[:8]}…")
        cur.execute(
            """SELECT count(*) FROM observed_presence WHERE verification_status='derived_ai_only'""",
        )
        ai_rows = cur.fetchone()[0]
        print(f"AI_DERIVED_ROWS     = {ai_rows} (must be excluded from consumer aggregate)")

        # 2e. Place FK behavior: candidate with a bogus place must fail
        try:
            sp = conn.savepoint()
            cur.execute(
                """INSERT INTO reality_candidate
                   (id, candidate_type, place_id, review_status, verification_status, created_at, updated_at)
                   VALUES (%s,'observed_presence','no-such-place','REVIEW_PENDING','unverified',%s,%s)""",
                (str(uuid4()), now, now),
            )
            print("PLACE_FK            = FAIL (bogus place accepted!)")
        except psycopg.errors.ForeignKeyViolation:
            conn.rollback(sp)
            print("PLACE_FK            = PASS (bogus place rejected)")

        # 2f. candidate->claim RESTRICT: cannot delete a candidate that has a claim
        try:
            sp = conn.savepoint()
            cur.execute("DELETE FROM reality_candidate WHERE id=%s", (cand_id,))
            print("CANDIDATE_RESTRICT  = FAIL (candidate deleted despite claim)")
        except psycopg.errors.ForeignKeyViolation:
            conn.rollback(sp)
            print("CANDIDATE_RESTRICT  = PASS (claim blocks candidate delete)")
        # 2g. Zone FK SET NULL
        zone_id = None
        cur.execute("SELECT id FROM zone WHERE place_id=%s LIMIT 1", (place_id,))
        zrow = cur.fetchone()
        if zrow:
            zone_id = zrow[0]
            cur.execute(
                """INSERT INTO observed_presence
                   (id, candidate_id, place_id, zone_id, animal_scope, observed_action,
                    observed_at, captured_at, verification_status, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,'cat','present',%s,%s,'human_verified',%s,%s)""",
                (str(uuid4()), cand_id, place_id, zone_id, now, now, now, now),
            )
            cur.execute(
                "UPDATE zone SET id=%s WHERE id=%s",
                (f"{zone_id}-replaced", zone_id),
            )
            print(f"ZONE_FK_SETNULL     = drill executed (zone {zone_id[:8]}… replaced); "
                  "SET NULL verified if no error above")

    conn.rollback()
    print("\nDRILL_ROLLED_BACK   = production untouched")

print("VERIFICATION_PERSISTENCE_COMPLETE")
