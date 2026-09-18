"""Locks for the place-coordinate backfill's matching rules.

These are pure functions, so they can be tested without network or database.
They matter because the failure mode of a sloppy matcher is silent: a plausible
coordinate in the wrong place still looks like a successful backfill, and a
rule-bearing place ends up being returned by /places/nearby for a query that is
somewhere else entirely.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import place_geo_backfill as geo  # noqa: E402


def test_name_match_uses_the_longest_shared_ngram():
    """The venue name is what proves the hit; longer match wins."""
    assert (
        geo.name_matches("世纪公园", "世纪公园, 1001, 花木街道, 浦东新区, 上海市, 中国")
        == "世纪公园"
    )
    assert geo.name_matches("上海动物园", "上海动物园, 2381, 虹桥路, 长宁区") == "上海动物园"


def test_name_match_ignores_the_parenthetical_disambiguator():
    """'西岸梦中心（Gate M）' must still match '西岸梦中心'."""
    assert geo.name_matches("西岸梦中心（Gate M）", "西岸梦中心, 龙华街道, 徐汇区") == "西岸梦中心"
    assert geo.clean_name("CHARLIE'S 粉红汉堡（马当路店）") == "CHARLIE'S 粉红汉堡"


def test_name_match_rejects_an_unrelated_hit():
    """A hit that merely shares the city must not validate."""
    assert geo.name_matches("世纪公园", "上海市, 中国") is None
    assert geo.name_matches("兴业太古汇", "南京西路街道, 静安区, 上海市, 中国") is None


def test_address_queries_extract_the_venue_after_the_house_number():
    """'中海环宇荟' is the mall; the leading '号' would make the query miss."""
    q = geo.address_queries("上海市黄浦区马当路441号中海环宇荟地上一层L33室")
    assert "中海环宇荟" in q
    assert "马当路441号" in q
    assert not any(x.startswith("号") for x in q)
    full = "上海市黄浦区马当路441号中海环宇荟地上一层L33室"
    assert not any(x.startswith("上海市黄浦区") and x != full for x in q)


def test_address_queries_fall_back_to_the_full_address_first():
    """The full address is tried first — when it works it is the most precise."""
    q = geo.address_queries("上海市闵行区浦江郊野公园滨江漫步区（闵浦二桥下）")
    assert q[0] == "上海市闵行区浦江郊野公园滨江漫步区"


def test_longest_common_finds_the_venue():
    assert (
        geo.longest_common("中海环宇荟", "中海环宇荟, 卢家湾, 打浦桥街道, 上海市, 黄浦区")
        == "中海环宇荟"
    )


def test_longest_common_rejects_district_level_overlap():
    """'上海市' is shared by every Shanghai hit, so it must stay under the floor.

    The address stage requires a shared substring of at least 4 characters; a
    city/district-level overlap is 3 and is therefore refused.
    """
    assert len(geo.longest_common("上海市黄浦区马当路", "马当路, 新天地, 上海市, 黄浦区")) <= 3
    assert len(geo.longest_common("上海市黄浦区马当路", "南京西路, 静安区, 上海市")) <= 3


def test_shanghai_bbox_contains_the_seed_center_and_rejects_other_cities():
    assert geo.SHANGHAI_BBOX["lat_min"] < geo.CENTER[0] < geo.SHANGHAI_BBOX["lat_max"]
    # Qingdao — the OSM hit for a same-named mall elsewhere.
    assert not (geo.SHANGHAI_BBOX["lat_min"] <= 36.13 <= geo.SHANGHAI_BBOX["lat_max"])
