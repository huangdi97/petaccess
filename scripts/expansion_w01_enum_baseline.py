"""Wave 01 step 0: enumerate the real-place baseline in the production database.

Read-only. Prints a JSON blob; writes nothing.
"""

from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("PYTHONPATH", "")
os.environ["DB_ROLE"] = "PRODUCTION"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "api"))

from sqlalchemy import text  # noqa: E402

from app.db.session import get_session_factory  # noqa: E402

Q_PLACES = """
SELECT p.id, p.canonical_name, p.place_type, p.canonical_address,
       p.lifecycle_status, p.alias_names,
       ST_AsText(p.location) AS loc,
       ST_X(p.location::geometry) AS lng,
       ST_Y(p.location::geometry) AS lat,
       o.name AS operator_name
FROM place p
LEFT JOIN operator o ON o.id = p.operator_id
ORDER BY p.canonical_name
"""

Q_RULES = """
SELECT r.id, r.place_id, r.zone_id, r.animal_scope, r.action, r.effect,
       r.rule_layer, r.mandatory_level, r.status, r.source_scope_exact,
       r.subject_scope_normalized, r.normalization_type, r.normative_effect,
       r.review_due_at, r.last_verified_at, r.jurisdiction_code
FROM access_rule r
ORDER BY r.place_id, r.animal_scope
"""

Q_ZONES = """
SELECT z.id, z.place_id, z.name, z.zone_type, z.floor_ref, z.indoor_outdoor
FROM zone z ORDER BY z.place_id, z.name
"""

Q_SOURCES = """
SELECT s.id, s.source_type, s.issuer, s.issuer_verification, s.source_url,
       s.directness, s.spatial_precision, s.collected_at, s.published_at
FROM source s ORDER BY s.source_type, s.issuer
"""

Q_CANDIDATES = """
SELECT c.id, c.place_id, c.zone_id, c.animal_scope, c.action, c.effect,
       c.rule_layer, c.review_status, c.evidence_bundle_id, c.source_id,
       c.extraction_method, c.published_rule_id
FROM rule_candidate c ORDER BY c.review_status, c.place_id
"""

Q_COUNTS = """
SELECT 'place' AS t, count(*) FROM place
UNION ALL SELECT 'zone', count(*) FROM zone
UNION ALL SELECT 'access_rule', count(*) FROM access_rule
UNION ALL SELECT 'rule_exception', count(*) FROM rule_exception
UNION ALL SELECT 'source', count(*) FROM source
UNION ALL SELECT 'source_artifact', count(*) FROM source_artifact
UNION ALL SELECT 'evidence_bundle', count(*) FROM evidence_bundle
UNION ALL SELECT 'rule_candidate', count(*) FROM rule_candidate
UNION ALL SELECT 'observation_candidate', count(*) FROM observation_candidate
UNION ALL SELECT 'source_monitor', count(*) FROM source_monitor
UNION ALL SELECT 'freshness_policy', count(*) FROM freshness_policy
UNION ALL SELECT 'data_source_job', count(*) FROM data_source_job
UNION ALL SELECT 'data_license', count(*) FROM data_license
UNION ALL SELECT 'amenity', count(*) FROM amenity
UNION ALL SELECT 'entrance', count(*) FROM entrance
UNION ALL SELECT 'access_path', count(*) FROM access_path
UNION ALL SELECT 'organization', count(*) FROM organization
UNION ALL SELECT 'policy_template', count(*) FROM policy_template
UNION ALL SELECT 'event_policy', count(*) FROM event_policy
UNION ALL SELECT 'operator', count(*) FROM operator
UNION ALL SELECT 'external_place_ref', count(*) FROM external_place_ref
"""


def rows(s, q):
    return [dict(r) for r in s.execute(text(q)).mappings().all()]


def main() -> int:
    s = get_session_factory()()
    try:
        out = {
            "counts": {r["t"]: r["count"] for r in rows(s, Q_COUNTS)},
            "places": rows(s, Q_PLACES),
            "zones": rows(s, Q_ZONES),
            "rules": rows(s, Q_RULES),
            "sources": rows(s, Q_SOURCES),
            "candidates": rows(s, Q_CANDIDATES),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
