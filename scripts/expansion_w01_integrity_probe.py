"""Wave 01 收口诊断：孤儿 Source 归属 + 审计 target_id 分组 + 已发布场所解析快照。

只读脚本，不改任何数据。
"""

from __future__ import annotations

import json
import os

import sqlalchemy as sa

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess",
)


def main() -> None:
    engine = sa.create_engine(DATABASE_URL)
    out: dict[str, object] = {}
    with engine.connect() as c:
        cols = [
            r[0]
            for r in c.execute(
                sa.text(
                    "select column_name from information_schema.columns "
                    "where table_name='source' order by ordinal_position"
                )
            )
        ]
        out["source_columns"] = cols

        orphan_sql = """
            select s.*
            from source s
            where not exists (select 1 from evidence_bundle b where b.source_id = s.id)
              and not exists (select 1 from source_artifact a where a.source_id = s.id)
              and not exists (select 1 from rule_candidate c where c.source_id = s.id)
              and not exists (select 1 from access_rule r where r.source_id = s.id)
              and not exists (select 1 from rule_exception e where e.source_id = s.id)
        """
        orphans = [dict(r._mapping) for r in c.execute(sa.text(orphan_sql))]
        for o in orphans:
            for k, v in list(o.items()):
                if hasattr(v, "isoformat"):
                    o[k] = v.isoformat()
        out["orphan_sources"] = orphans

        # Wave01 引入的 source 是否全都非空挂
        wave_sql = """
            select count(*) from source
            where id in (select source_id from rule_candidate where expansion_run_id = :run)
               or id in (select source_id from evidence_bundle where expansion_run_id = :run)
        """
        out["wave01_sources_with_usage"] = c.execute(
            sa.text(wave_sql), {"run": "EXP-R1-W01-20260918"}
        ).scalar_one()

        # 审计 target_id 不可用分组
        audit_sql = """
            select target_type, count(*) as rows_with_broken_target_id,
                   min(created_at) as earliest, max(created_at) as latest
            from audit_log where target_id = 'None' group by 1 order by 2 desc
        """
        audit_rows = [dict(r._mapping) for r in c.execute(sa.text(audit_sql))]
        for r in audit_rows:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        out["audit_target_unusable"] = audit_rows

        # 已发布场所
        pub_sql = """
            select p.*
            from place p
            where exists (select 1 from access_rule r where r.place_id = p.id
                          and r.status = 'current')
            order by p.id
        """
        pubs = [dict(r._mapping) for r in c.execute(sa.text(pub_sql))]
        for r in pubs:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
                elif k in ("geom", "location", "centroid", "point"):
                    r[k] = "<geom>"
        out["published_places"] = pubs

        # 每个已发布场所的规则指纹
        fp_sql = """
            select r.*
            from access_rule r
            where r.status = 'current'
            order by r.place_id, r.id
        """
        rows = [dict(r._mapping) for r in c.execute(sa.text(fp_sql))]
        for r in rows:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        out["published_rules"] = rows

        ex_sql = """
            select e.*
            from rule_exception e
            order by e.id
        """
        exs = [dict(r._mapping) for r in c.execute(sa.text(ex_sql))]
        for r in exs:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
        out["published_exceptions"] = exs

        # zone 指纹
        zone_sql = """
            select z.*
            from zone z
            where z.place_id in (select place_id from access_rule where status='current'
                                 and place_id is not null)
            order by z.place_id, z.id
        """
        zone_rows = [dict(r._mapping) for r in c.execute(sa.text(zone_sql))]
        for r in zone_rows:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
                elif k in ("geom", "geometry"):
                    r[k] = "<geom>"
        out["published_place_zones"] = zone_rows

    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
