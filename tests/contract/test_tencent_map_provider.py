"""TencentMapProvider fixture contract tests (PROVIDER_HARDENING_SPEC).

No network: every scenario uses an httpx.MockTransport fixture emulating the
Tencent WebService API. A real key live smoke stays BLOCKED_EXTERNAL (B-04).
"""

import httpx
import pytest

from app.providers.tencent_map import ProviderError, TencentMapProvider

KEY = "test-key-abc123"  # fixture-only; never a real credential


def make_provider(handler) -> TencentMapProvider:
    transport = httpx.MockTransport(handler)
    return TencentMapProvider(KEY, timeout_seconds=0.5, max_retries=1, transport=transport)


def ok(payload: dict) -> httpx.Response:
    return httpx.Response(200, json={"status": 0, "message": "query ok", **payload})


def test_search_success_normalizes_pois():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=test-key-abc123" in str(request.url)
        assert "boundary=nearby(31.23%2C121.47%2C1000%2C1)" in str(
            request.url
        ) or "boundary=nearby" in str(request.url)
        return ok(
            {
                "data": [
                    {
                        "id": "poi-1",
                        "title": "星河咖啡",
                        "address": "演示路 1 号",
                        "location": {"lat": 31.2301, "lng": 121.4701},
                    },
                ]
            }
        )

    provider = make_provider(handler)
    places = provider.search_places("咖啡", 31.23, 121.47, 1000)
    assert len(places) == 1
    p = places[0]
    assert p.name == "星河咖啡"
    assert p.provider == "tencent"
    assert p.external_id == "poi-1"  # external reference only — never a place PK


def test_search_empty_is_empty_list():
    provider = make_provider(lambda req: ok({"data": []}))
    assert provider.search_places("不存在", 31.23, 121.47, 500) == []


def test_search_blank_keyword_short_circuits_without_http():
    sentinel = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal sentinel
        sentinel = True
        return ok({"data": []})

    provider = make_provider(handler)
    assert provider.search_places("  ", 31.23, 121.47, 500) == []
    assert sentinel is None  # no HTTP call made


def test_auth_error_normalized_and_key_redacted():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": 110, "message": "请求来源未被授权 " + KEY})

    provider = make_provider(handler)
    with pytest.raises(ProviderError) as ei:
        provider.search_places("x", 31.23, 121.47, 500)
    assert ei.value.code == "auth_failed"
    # secret redaction: normalized message never contains the raw key
    assert KEY not in str(ei.value)
    assert KEY not in ei.value.message


def test_quota_error_normalized():
    provider = make_provider(
        lambda req: httpx.Response(
            200, json={"status": 120, "message": "此key每日调用量已达到上限"}
        )
    )
    with pytest.raises(ProviderError) as ei:
        provider.reverse_geocode(31.23, 121.47)
    assert ei.value.code == "quota_exceeded"


def test_bad_request_normalized():
    provider = make_provider(
        lambda req: httpx.Response(200, json={"status": 310, "message": "请求参数非法"})
    )
    with pytest.raises(ProviderError) as ei:
        provider.search_places("x", 31.23, 121.47, 500)
    assert ei.value.code == "bad_request"


def test_malformed_json_normalized():
    provider = make_provider(lambda req: httpx.Response(200, content=b"<html>not json</html>"))
    with pytest.raises(ProviderError) as ei:
        provider.reverse_geocode(31.23, 121.47)
    assert ei.value.code == "malformed_response"


def test_timeout_maps_to_network_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    provider = make_provider(handler)
    with pytest.raises(ProviderError) as ei:
        provider.reverse_geocode(31.23, 121.47)
    assert ei.value.code == "network_timeout"


def test_transient_5xx_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        return ok(
            {"result": {"address": "演示市某路", "formatted_addresses": {"recommend": "某路口"}}}
        )

    provider = make_provider(handler)
    result = provider.reverse_geocode(31.23, 121.47)
    assert calls["n"] == 2
    assert result["provider"] == "tencent"


def test_permanent_5xx_raises_after_retries():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500)

    provider = make_provider(handler)
    with pytest.raises(ProviderError) as ei:
        provider.search_places("x", 31.23, 121.47, 500)
    assert calls["n"] == 2  # max_retries=1 → 2 attempts total
    assert ei.value.code == "provider_unavailable"


def test_render_config_never_contains_key():
    provider = make_provider(lambda req: ok({"data": []}))
    cfg = provider.render_config()
    assert cfg["provider"] == "tencent"
    assert KEY not in str(cfg)
    assert "key" not in str(cfg).lower().replace("key_configured", "")


def test_navigation_deep_link_shape():
    provider = make_provider(lambda req: ok({"data": []}))
    nav = provider.open_navigation(31.23, 121.47, "星河咖啡")
    assert nav["action"] == "open_url"
    assert "uri/v1/routeplan" in nav["url"]
    assert "31.23" in nav["url"] and "121.47" in nav["url"]


def test_radius_clamped_to_provider_limits():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return ok({"data": []})

    provider = make_provider(handler)
    provider.search_places("x", 31.23, 121.47, 999999)
    assert "999999" not in seen["url"]
    assert "10000" in seen["url"]
