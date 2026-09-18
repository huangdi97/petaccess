"""Backfill ``place.location`` for places that have no coordinates.

Why this exists
---------------
``/places/nearby`` filters on ``Place.location IS NOT NULL`` (services/api/app/api/v1/places.py).
A place without coordinates is therefore not merely "harder to find" — it is
**silently absent** from nearby search, with no hint to the caller that the
place exists at all. After BATCH_02 that would hide 6 places carrying 7
published rules.

What this script is NOT
-----------------------
Coordinates are place geometry, not an access rule. Backfilling them cannot
change any resolver answer, and this script never touches rule data. It is
still a production write, so it is gated exactly like the other production
scripts: explicit ``--production-confirm`` plus a human ``--reviewer``.

Source and honesty about precision
----------------------------------
There is no map-provider key configured in this environment
(``MAP_PROVIDER=mock``, ``TENCENT_MAP_KEY_SERVER`` empty), so geocoding uses
OpenStreetMap Nominatim (ODbL). Every proposal keeps its provenance —
``osm_type``/``osm_id``/``display_name``/query/fetch time — so a reviewer can
check the hit instead of trusting it.

Precision is graded, never glossed:

* ``AUTO_MATCHED`` — top hit is inside the Shanghai bbox AND the place name
  appears in the OSM ``display_name``.
* ``NEEDS_HUMAN`` — nothing matched plausibly. **Never applied.** A small shop
  inside a mall is often absent from OSM; guessing a nearby coordinate would
  put a rule-bearing place at a wrong address, which is worse than leaving it
  unlocated.

Usage::

    # 1. plan (read-only against the DB, writes only the proposals file)
    python scripts/place_geo_backfill.py --db-name petaccess --plan

    # 2. apply (production write; refuse without --production-confirm)
    python scripts/place_geo_backfill.py --db-name petaccess --apply \
        --reviewer <署名> --production-confirm

    # 3. verify what is still missing
    python scripts/place_geo_backfill.py --db-name petaccess --verify
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

import httpx  # noqa: E402
import psycopg  # noqa: E402
from psycopg.types.json import Json  # noqa: E402

from app.core.audit_events import AuditEvent  # noqa: E402
from app.db.safety import DatabaseRole, classify_database_name, guard_for_psycopg  # noqa: E402

PROPOSALS = REPO / "docs" / "expansion" / "place_geo_backfill_proposals.json"
REGISTER = REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01_publishable.json"

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "petaccess-place-geo-backfill/1.0 (local development; no bulk download)"
# Nominatim usage policy: at most one request per second, no parallel queries.
POLITE_DELAY_S = 1.1

# Shanghai administrative bounding box, generous enough for 崇明/横沙 but tight
# enough to reject an obvious wrong-city hit.
SHANGHAI_BBOX = {"lat_min": 30.65, "lat_max": 31.90, "lng_min": 120.80, "lng_max": 122.10}
# 人民广场 — only used as a sanity hint, never as a decision rule.
CENTER = (31.2304, 121.4737)

_PARENS = re.compile(r"[（(].*?[)）]")


def connect(db_name: str) -> psycopg.Connection:
    url = (
        f"postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/{db_name}"
        if "/" not in db_name
        else db_name
    )
    return psycopg.connect(url)


def clean_name(name: str) -> str:
    """Drop the parenthetical disambiguator: 'X（马当路店）' -> 'X'."""
    return _PARENS.sub("", name).strip()


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    from math import asin, cos, radians, sin, sqrt

    lat1, lon1 = radians(a[0]), radians(a[1])
    lat2, lon2 = radians(b[0]), radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def name_matches(canonical: str, display_name: str) -> str | None:
    """Return the matched substring, or None.

    Chinese place names have no word boundaries, so the test is "does an n-gram
    of the canonical name occur in the OSM display name", longest first.
    """
    target = clean_name(canonical)
    if not target:
        return None
    for size in (6, 5, 4, 3):
        for i in range(len(target) - size + 1):
            gram = target[i : i + size]
            if gram in display_name:
                return gram
    return None


_VENUE = re.compile(r"[\u4e00-\u9fa5]{2,8}(?:荟|中心|广场|天地|坊|公园|园|里|湾|城|汇|街|路|大道)")
_ROADNO = re.compile(r"[\u4e00-\u9fa5]{2,4}(?:路|街|大道)\d+号")
# "上海市黄浦区" prefix — stripped before venue extraction, otherwise the venue
# regex swallows the mall name and returns "上海市黄浦区马当路" instead.
_ADMIN = re.compile(r"^(?:上海市)?(?:[\u4e00-\u9fa5]{2,4}区)?")


def address_queries(address: str) -> list[str]:
    """Escalating queries derived from a canonical address, most specific last.

    A full Chinese address string almost never geocodes as-is. What does
    geocode is the venue inside it ('中海环宇荟'), or the road plus house
    number ('马当路441号'). The full address is tried first anyway — when it
    works it is the most precise answer available.
    """
    addr = _PARENS.sub("", address or "").strip()
    if not addr:
        return []
    out = [addr]
    local = _ADMIN.sub("", addr) or addr
    # A venue name usually sits right after the house number ("...441号中海环宇荟
    # 地上一层L33室"), so seed the search there as well as on the whole string.
    seeds = [local]
    if "号" in local:
        seeds.append(local.split("号", 1)[1])
    venue: list[str] = []
    for seed in seeds:
        venue.extend(_VENUE.findall(seed))
    # Drop tokens that merely start at a noise character — "号中海环宇荟" is the
    # mall reached through the house number, and the leading 号 would make the
    # query miss. Also drop anything carrying digits.
    venue = [v for v in venue if not re.search(r"\d", v) and v[0] not in "号层室地内上楼座弄幢"]
    if venue:
        out.append(max(venue, key=len))
    roadno = _ROADNO.search(local)
    if roadno:
        out.append(roadno.group(0))
    return list(dict.fromkeys(out))


def longest_common(a: str, b: str) -> str:
    """Longest substring shared by two strings (address strings are short)."""
    best = ""
    for i in range(len(a)):
        # longest first, so the first hit at this offset is the best one here
        for j in range(len(a) - i, 0, -1):
            sub = a[i : i + j]
            if sub in b:
                if len(sub) > len(best):
                    best = sub
                break
    return best


def geocode(
    client: httpx.Client, canonical: str, canonical_address: str | None = None
) -> dict[str, Any]:
    """Query Nominatim; return the best bbox-valid, name-matching hit.

    Two stages, deliberately separated because they carry different precision:

    1. **name** — the OSM display name contains the place name. This pins the
       actual venue.
    2. **address** — only for places OSM does not know (small shops inside a
       mall). Uses the place's own ``canonical_address`` and requires a road /
       landmark token from that address to appear in the hit. That lands the
       point on the right street, not necessarily on the right shop unit, so it
       is recorded as ``ADDRESS_LEVEL`` and never disguised as a name match.
    """
    queries = [f"上海市 {canonical}"]
    cleaned = clean_name(canonical)
    if cleaned and cleaned != canonical:
        queries.append(f"上海市 {cleaned}")
    queries.append(cleaned or canonical)

    seen: set[str] = set()
    attempts: list[dict[str, Any]] = []

    def run(q: str) -> list[dict[str, Any]]:
        try:
            resp = client.get(
                NOMINATIM,
                params={"q": q, "format": "json", "limit": 5, "accept-language": "zh-CN"},
                headers={"User-Agent": USER_AGENT},
                timeout=20.0,
            )
            resp.raise_for_status()
            hits = resp.json()
        except Exception as exc:  # network/JSON failure — recorded, never guessed
            attempts.append({"query": q, "error": f"{type(exc).__name__}: {exc}"})
            time.sleep(POLITE_DELAY_S)
            return []

        ranked: list[dict[str, Any]] = []
        for hit in hits:
            lat = float(hit["lat"])
            lon = float(hit["lon"])
            in_bbox = (
                SHANGHAI_BBOX["lat_min"] <= lat <= SHANGHAI_BBOX["lat_max"]
                and SHANGHAI_BBOX["lng_min"] <= lon <= SHANGHAI_BBOX["lng_max"]
            )
            ranked.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "in_bbox": in_bbox,
                    "matched_gram": name_matches(canonical, hit.get("display_name", "")),
                    "display_name": hit.get("display_name"),
                    "osm_type": hit.get("osm_type"),
                    "osm_id": hit.get("osm_id"),
                    "class": hit.get("class"),
                    "type": hit.get("type"),
                    "addresstype": hit.get("addresstype"),
                    "importance": hit.get("importance"),
                    "query": q,
                }
            )
        attempts.append({"query": q, "hits": ranked})
        return ranked

    def finish(best: dict[str, Any], *, status: str, method: str, basis: str) -> dict[str, Any]:
        best.update(
            {
                "status": status,
                "match_method": method,
                "geocode_basis": basis,
                "distance_from_center_km": round(
                    haversine_km(CENTER, (best["lat"], best["lon"])), 2
                ),
                "licence": "Data © OpenStreetMap contributors, ODbL 1.0",
                "provider": "OpenStreetMap Nominatim",
                "fetched_at": datetime.now(UTC).isoformat(),
            }
        )
        # Copy before attaching `attempts`: `best` is itself one of the hits
        # inside `attempts`, so attaching in place would make the payload a
        # circular reference and json.dumps would raise.
        result = dict(best)
        result["attempts"] = attempts
        return result

    # ---- stage 1: the venue itself is in OSM ------------------------------
    for q in queries:
        if q in seen:
            continue
        seen.add(q)
        good = [h for h in run(q) if h["in_bbox"] and h["matched_gram"]]
        if good:
            good.sort(key=lambda h: (-len(h["matched_gram"]), -(h["importance"] or 0)))
            best = good[0]
            return finish(
                best,
                status="AUTO_MATCHED",
                method=f"n-gram {best['matched_gram']!r} in display_name",
                basis="canonical_name",
            )
        time.sleep(POLITE_DELAY_S)

    # ---- stage 2: fall back to the place's own address --------------------
    if canonical_address:
        for q in address_queries(canonical_address):
            if q in seen:
                continue
            seen.add(q)
            scored: list[tuple[int, float, str, dict[str, Any]]] = []
            for h in run(q):
                if not h["in_bbox"]:
                    continue
                gram = longest_common(q, h["display_name"] or "")
                # 4 characters is the floor: '上海市' / '黄浦区' shared by every
                # Shanghai hit would otherwise validate a district centroid.
                if len(gram) >= 4:
                    scored.append((len(gram), -(h["importance"] or 0), gram, h))
            if scored:
                scored.sort(reverse=True)
                _, _, gram, best = scored[0]
                return finish(
                    best,
                    status="ADDRESS_LEVEL",
                    method=f"address query {q[:24]!r} -> {gram!r} in display_name",
                    basis="canonical_address",
                )
            time.sleep(POLITE_DELAY_S)

    return {
        "status": "NEEDS_HUMAN",
        "reason": (
            "no OSM hit inside the Shanghai bbox matching either the place name"
            " or a road/landmark token from its canonical address"
        ),
        "attempts": attempts,
        "provider": "OpenStreetMap Nominatim",
        "fetched_at": datetime.now(UTC).isoformat(),
    }


def load_places(cur: Any) -> list[dict[str, Any]]:
    cur.execute(
        """
        select p.id, p.canonical_name, p.canonical_address,
               p.location is null as missing_geo,
               (select count(*) from access_rule ar
                 where ar.place_id = p.id and ar.status = 'current') as published_rules
        from place p
        where p.location is null
        order by p.canonical_name
        """
    )
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]


def plan(db_name: str | None, *, use_register: bool, out: Path) -> int:
    if use_register:
        rows = json.loads(REGISTER.read_text(encoding="utf-8"))["rows"]
        names: list[str] = []
        for r in rows:
            n = r.get("place_name")
            if n and n not in names:
                names.append(n)
        places = [
            {"id": None, "canonical_name": n, "canonical_address": None, "published_rules": None}
            for n in names
        ]
        print(f"PLACE_GEO_PLAN source=register count={len(places)}")
    else:
        assert db_name, "--db-name is required unless --source register"
        with connect(db_name) as conn, conn.cursor() as cur:
            places = load_places(cur)
        print(f"PLACE_GEO_PLAN source=db({db_name}) missing_geo={len(places)}")

    # trust_env=True: honour HTTP(S)_PROXY. With trust_env=False every external
    # request silently times out in proxied environments and every place lands
    # in NEEDS_HUMAN — which looks like "OSM has no data" but is really "we
    # never reached OSM".
    client = httpx.Client(trust_env=True)
    proposals: list[dict[str, Any]] = []
    try:
        for p in places:
            res = geocode(client, p["canonical_name"], p.get("canonical_address"))
            res["place_id"] = p["id"]
            res["canonical_name"] = p["canonical_name"]
            res["canonical_address"] = p["canonical_address"]
            res["published_rules"] = p["published_rules"]
            proposals.append(res)
            flag = {"AUTO_MATCHED": "OK ", "ADDRESS_LEVEL": "~A "}.get(res["status"], "?? ")
            tail = (
                f"{res['lat']:.6f},{res['lon']:.6f}  {res.get('display_name', '')[:48]}"
                if res["status"] == "AUTO_MATCHED"
                else res.get("reason", "")
            )
            print(f"  {flag}{p['canonical_name'][:28]:30s} {tail}")
    finally:
        client.close()

    payload = {
        "_schema": (
            "place coordinate backfill proposals. `status` is AUTO_MATCHED "
            "(venue found by name), ADDRESS_LEVEL (venue absent from OSM; pinned "
            "by its own address) or NEEDS_HUMAN (never applied). "
            "or NEEDS_HUMAN (never applied). Coordinates come from OpenStreetMap "
            "Nominatim; each row keeps its OSM provenance so a reviewer can verify "
            "the hit. This file is geometry only — it cannot change any access rule."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": "OpenStreetMap Nominatim (ODbL 1.0)",
        "bbox": SHANGHAI_BBOX,
        "proposals": proposals,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for p in proposals:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    summary = "  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"\nwrote {out.relative_to(REPO)}  {summary}")
    return 0


def apply_backfill(
    db_name: str, *, reviewer: str, production_confirm: bool, proposals: Path
) -> int:
    role = classify_database_name(db_name)
    if role is DatabaseRole.PRODUCTION and not production_confirm:
        raise SystemExit(
            "refusing to write to PRODUCTION without --production-confirm "
            "(coordinate backfill is reversible but it is still a live write)"
        )
    if not reviewer or reviewer.lower() in {"ai", "system", "auto", "drill", "agent"}:
        raise SystemExit("--reviewer must name the human who authorised this write")

    payload = json.loads(proposals.read_text(encoding="utf-8"))
    applyable = {"AUTO_MATCHED", "ADDRESS_LEVEL"}
    usable = [p for p in payload["proposals"] if p["status"] in applyable]

    with connect(db_name) as conn:
        guard_for_psycopg(conn)  # refuses unknown/unregistered databases
        with conn.cursor() as cur:
            cur.execute("select current_database()")
            print(f"target database = {cur.fetchone()[0]}  (role={role.value})")

            applied: list[dict[str, Any]] = []
            skipped_not_null = 0
            skipped_no_match = 0
            for p in usable:
                cur.execute(
                    "select id, canonical_name, location is null from place"
                    " where canonical_name = %s",
                    (p["canonical_name"],),
                )
                row = cur.fetchone()
                if row is None:
                    skipped_no_match += 1
                    continue
                place_id, canonical_name, is_null = row
                if not is_null:
                    skipped_not_null += 1
                    continue
                cur.execute(
                    "update place set location = ST_SetSRID(ST_MakePoint(%s, %s), 4326)"
                    " where id = %s",
                    (p["lon"], p["lat"], place_id),
                )
                cur.execute(
                    "insert into audit_log (id, actor_user_id, actor_role, action, target_type,"
                    " target_id, before_state, after_state, detail, created_at)"
                    " values (%s,%s,%s,%s,%s,%s,%s,%s,%s,now())",
                    (
                        str(uuid.uuid4()),
                        None,
                        f"human:{reviewer}",
                        AuditEvent.PLACE_UPDATE.value,
                        "place",
                        str(place_id),
                        Json({"location": None}),
                        Json({"location": {"lat": p["lat"], "lng": p["lon"]}}),
                        Json(
                            {
                                "reason": (
                                    "PLACE_GEO_PENDING — place was invisible to /places/nearby"
                                ),
                                "source": {
                                    "provider": p.get("provider"),
                                    "licence": p.get("licence"),
                                    "osm_type": p.get("osm_type"),
                                    "osm_id": p.get("osm_id"),
                                    "display_name": p.get("display_name"),
                                    "query": p.get("query"),
                                    "fetched_at": p.get("fetched_at"),
                                },
                                "match_method": p.get("match_method"),
                                "geocode_basis": p.get("geocode_basis"),
                                "precision": (
                                    "name_level"
                                    if p["status"] == "AUTO_MATCHED"
                                    else "address_level"
                                ),
                                "reviewer": reviewer,
                            }
                        ),
                    ),
                )
                applied.append(
                    {
                        "place_id": place_id,
                        "canonical_name": canonical_name,
                        "lat": p["lat"],
                        "lng": p["lon"],
                        "osm_id": p.get("osm_id"),
                        "display_name": p.get("display_name"),
                    }
                )
            conn.commit()

            cur.execute("select count(*) from place")
            total = cur.fetchone()[0]
            cur.execute("select count(*) from place where location is null")
            still_missing = cur.fetchone()[0]

    print("PLACE_GEO_APPLY")
    for a in applied:
        print(
            f"  SET {a['canonical_name'][:28]:30s} {a['lat']:.6f},{a['lng']:.6f}  osm={a['osm_id']}"
        )
    print(
        f"  applied={len(applied)} already_had_coords={skipped_not_null}"
        f" no_such_place={skipped_no_match}"
    )
    print(f"  places={total} still_missing_geo={still_missing}")
    return 0


def verify(db_name: str) -> int:
    with connect(db_name) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from place")
        total = cur.fetchone()[0]
        cur.execute("select count(*) from place where location is null")
        missing = cur.fetchone()[0]
        cur.execute(
            """
            select p.canonical_name,
                   (select count(*) from access_rule ar
                     where ar.place_id = p.id and ar.status = 'current') as rules
            from place p where p.location is null
            order by rules desc, p.canonical_name
            """
        )
        rows = cur.fetchall()
    print(f"PLACE_GEO_VERIFY db={db_name} places={total} missing_geo={missing}")
    for name, rules in rows:
        print(f"  MISSING rules={rules}  {name}")
    print(f"  discoverable_by_nearby={total - missing}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--db-name")
    ap.add_argument("--plan", action="store_true", help="geocode and write proposals (no DB write)")
    ap.add_argument(
        "--apply", action="store_true", help="write coordinates for AUTO_MATCHED proposals"
    )
    ap.add_argument("--verify", action="store_true", help="report remaining coordinate gaps")
    ap.add_argument("--source", choices=("db", "register"), default="db")
    ap.add_argument("--proposals", default=str(PROPOSALS))
    ap.add_argument("--reviewer")
    ap.add_argument("--production-confirm", action="store_true")
    args = ap.parse_args(argv)

    if args.apply:
        return apply_backfill(
            args.db_name,
            reviewer=args.reviewer or "",
            production_confirm=args.production_confirm,
            proposals=Path(args.proposals),
        )
    if args.verify:
        return verify(args.db_name)
    return plan(args.db_name, use_register=args.source == "register", out=Path(args.proposals))


if __name__ == "__main__":
    raise SystemExit(main())
