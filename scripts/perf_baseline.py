"""Performance baseline probe (PART A A11).

Runs N sequential requests against the local stack and reports p50/p95 per
endpoint. Read-only endpoints only; uses the demo seed data.
"""

import json
import statistics
import time

import httpx

BASE = "http://127.0.0.1:8010"
N = 50
PLACE_ID = "8412b521-5e1c-505d-9dec-568acb860c76"  # 星河咖啡·测试店 (demo seed)
LAT, LNG = 31.2304, 121.4737

endpoints = [
    ("GET /health", "GET", "/health", None),
    ("GET /places?limit=20", "GET", "/api/v1/places?limit=20", None),
    (
        "GET /places/nearby r=3000",
        "GET",
        f"/api/v1/places/nearby?lat={LAT}&lng={LNG}&radius_m=3000&limit=30",
        None,
    ),
    ("GET /places/{id} detail", "GET", f"/api/v1/places/{PLACE_ID}", None),
    ("GET /places/{id}/zones", "GET", f"/api/v1/places/{PLACE_ID}/zones", None),
    (
        "POST /rules/evaluate",
        "POST",
        "/api/v1/rules/evaluate",
        {
            "place_id": PLACE_ID,
            "animal": {"species": "dog", "weight_kg": 9.5, "is_service_animal": False},
            "action": "enter",
        },
    ),
    ("GET answerability", "GET", f"/api/v1/places/{PLACE_ID}/answerability", None),
    ("GET /admin/candidates", "GET", "/api/v1/admin/candidates?limit=20", None),
    (
        "POST effective-rules",
        "POST",
        f"/api/v1/places/{PLACE_ID}/effective-rules",
        {},
    ),
]


def main() -> None:
    results: dict[str, list[float]] = {}
    errors: dict[str, str] = {}
    admin_headers: dict[str, str] = {}
    with httpx.Client(base_url=BASE, timeout=10.0, trust_env=False) as c:
        # authenticated endpoints: create a throwaway admin user
        email = f"perf-{int(time.time())}@example.com"
        r = c.post(
            "/api/v1/auth/register",
            json={"display_name": "perf", "email": email, "password": "passw0rd123"},
        )
        if r.status_code == 201:
            token = r.json()["access_token"]
            from app.db.session import get_session_factory
            from app.models import User

            s = get_session_factory()()
            row = s.query(User).filter(User.email == email).one()
            row.role = "admin"
            s.commit()
            s.close()
            admin_headers = {"Authorization": f"Bearer {token}"}
        for name, method, path, body in endpoints:
            times: list[float] = []
            for _ in range(N):
                t0 = time.perf_counter()
                try:
                    r = c.request(method, path, json=body, headers=admin_headers)
                    elapsed = (time.perf_counter() - t0) * 1000
                    if r.status_code >= 400:
                        errors[name] = f"HTTP {r.status_code} on {path}"
                        break
                    times.append(elapsed)
                except httpx.HTTPError as e:
                    errors[name] = f"{type(e).__name__}: {e}"
                    break
            if times:
                results[name] = times

    report = {}
    for name, times in results.items():
        times_sorted = sorted(times)
        report[name] = {
            "n": len(times),
            "p50_ms": round(statistics.median(times_sorted), 2),
            "p95_ms": round(times_sorted[int(len(times_sorted) * 0.95) - 1], 2),
            "mean_ms": round(statistics.mean(times_sorted), 2),
            "min_ms": round(min(times_sorted), 2),
            "max_ms": round(max(times_sorted), 2),
        }
    print(json.dumps({"endpoints": report, "errors": errors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
