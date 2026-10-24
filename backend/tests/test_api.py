"""API behaviour through FastAPI's TestClient. Validation errors are raised
before any data is loaded; tests that need a 200 response use `real_data`
so they skip cleanly when backend/data is missing."""
import pytest

ENDPOINTS = ["/api/series", "/api/metrics"]
ONE_DAY = {"start": "2026-01-15", "end": "2026-01-15"}


def test_health(client, real_data):
    actuals, _, n_forecasts = real_data
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "actuals": len(actuals), "forecast_rows": n_forecasts}
    assert len(actuals) > 0 and n_forecasts > 0


def test_meta(client):
    body = client.get("/api/meta").json()
    assert body["max_horizon"] == 40
    assert body["default_gate_closure"] == "09:20"
    assert body["first_day"] == "2026-01-01" and body["last_day"] == "2026-01-31"


@pytest.mark.parametrize("path", ENDPOINTS)
def test_start_after_end_is_400(client, path):
    res = client.get(path, params={"start": "2026-01-10", "end": "2026-01-05"})
    assert res.status_code == 400
    assert "start must be on or before end" in res.json()["detail"]


@pytest.mark.parametrize("path", ENDPOINTS)
@pytest.mark.parametrize("dates", [{"start": "2025-12-31", "end": "2026-01-05"},
                                   {"start": "2026-01-05", "end": "2026-02-01"}])
def test_dates_outside_january_are_400(client, path, dates):
    res = client.get(path, params=dates)
    assert res.status_code == 400
    assert "dates must be between" in res.json()["detail"]


@pytest.mark.parametrize("path", ENDPOINTS)
@pytest.mark.parametrize("horizon", [-1, 41, "abc"])
def test_horizon_out_of_range_is_422(client, path, horizon):
    assert client.get(path, params={"horizon": horizon}).status_code == 422


@pytest.mark.parametrize("path", ENDPOINTS)
@pytest.mark.parametrize("gate_closure", ["9:2", "9:20", "24:00", "09:60", "0920", "abc", ""])
def test_invalid_gate_closure_is_422(client, path, gate_closure):
    assert client.get(path, params={"gate_closure": gate_closure}).status_code == 422


def test_series_fixed_horizon(client, real_data):
    res = client.get("/api/series", params={**ONE_DAY, "horizon": 24})
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 48                                   # half-hourly actuals for one day
    assert set(rows[0]) == {"time", "actual", "forecast", "publishTime", "leadHours", "error"}
    assert sum(r["forecast"] is not None for r in rows) == 24
    assert all(r["leadHours"] >= 24 for r in rows if r["leadHours"] is not None)


def test_series_decision_time(client, real_data):
    res = client.get("/api/series", params={**ONE_DAY, "gate_closure": "09:20"})
    assert res.status_code == 200
    runs = {r["publishTime"] for r in res.json() if r["publishTime"]}
    assert len(runs) == 1
    assert runs.pop() <= "2026-01-14T09:20:00Z"


@pytest.mark.parametrize("params", [{"horizon": 24}, {"horizon": 1.5}, {"gate_closure": "09:20"},
                                    {"gate_closure": "11:00"}])
def test_metrics_valid_requests(client, real_data, params):
    res = client.get("/api/metrics", params={**ONE_DAY, **params})
    assert res.status_code == 200
    assert res.json()["count"] == 24


def test_gate_closure_overrides_horizon(client, real_data):
    a = client.get("/api/metrics", params={**ONE_DAY, "gate_closure": "09:20", "horizon": 2}).json()
    b = client.get("/api/metrics", params={**ONE_DAY, "gate_closure": "09:20", "horizon": 40}).json()
    assert a == b


def test_horizon_curve(client, real_data):
    res = client.get("/api/horizon-curve", params=ONE_DAY)
    assert res.status_code == 200
    assert [c["horizon"] for c in res.json()] == list(range(0, 41, 2))
