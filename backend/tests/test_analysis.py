from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.analysis import (MAX_HORIZON_HOURS, ForecastIndex, build_series, compute_metrics,
                          decision_cutoff, horizon_curve, percentile)
from app.main import app

T = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

FORECASTS = [
    # three forecast runs for the same target hour 2026-01-02 12:00
    {"publishTime": "2026-01-01T00:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 1000},
    {"publishTime": "2026-01-01T12:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 2000},
    {"publishTime": "2026-01-02T06:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 3000},
]
ACTUALS = [{"startTime": "2026-01-02T12:00:00Z", "generation": 2500}]


def test_picks_latest_forecast_published_before_horizon():
    idx = ForecastIndex(FORECASTS)
    target = T("2026-01-02T12:00:00")
    assert idx.latest_before(target, 4)[1] == 3000    # 06:00 run is 6h before
    assert idx.latest_before(target, 12)[1] == 2000   # 06:00 too late, 12:00 prev day ok
    assert idx.latest_before(target, 24)[1] == 2000   # exactly 24h before counts
    assert idx.latest_before(target, 30)[1] == 1000
    assert idx.latest_before(target, 48) is None      # nothing published that early


def test_series_and_error_sign():
    rows = build_series(ACTUALS, ForecastIndex(FORECASTS),
                        T("2026-01-02T00:00:00"), T("2026-01-03T00:00:00"), 24)
    assert rows[0]["forecast"] == 2000
    assert rows[0]["error"] == 500                    # actual - forecast
    assert rows[0]["leadHours"] == 24.0


def test_metrics():
    rows = [{"time": "2026-01-02T00:00:00Z", "actual": 100, "forecast": 90, "error": 10},
            {"time": "2026-01-02T01:00:00Z", "actual": 100, "forecast": 130, "error": -30}]
    m = compute_metrics(rows)
    assert m["count"] == 2
    assert m["mae"] == 20
    assert m["bias"] == -10
    assert m["max_shortfall"] == -30


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([0, 10], 10) == 1


def test_horizon_curve_capped_at_max_horizon():
    # add a run 60h ahead so every horizon up to 48h would have data without the cap
    forecasts = FORECASTS + [{"publishTime": "2025-12-31T00:00:00Z",
                              "startTime": "2026-01-02T12:00:00Z", "generation": 500}]
    curve = horizon_curve(ACTUALS, ForecastIndex(forecasts),
                          T("2026-01-02T00:00:00"), T("2026-01-03T00:00:00"))
    assert MAX_HORIZON_HOURS == 40
    assert [c["horizon"] for c in curve] == list(range(0, 41, 2))


def test_metrics_rejects_horizon_above_max():
    res = TestClient(app).get("/api/metrics", params={"horizon": 41})
    assert res.status_code == 422


def test_latest_at_or_before():
    idx = ForecastIndex(FORECASTS)
    target = T("2026-01-02T12:00:00")
    assert idx.latest_at_or_before(target, T("2026-01-01T12:00:00"))[1] == 2000   # exactly at cutoff counts
    assert idx.latest_at_or_before(target, T("2026-01-01T11:59:00"))[1] == 1000
    assert idx.latest_at_or_before(target, T("2026-01-03T00:00:00"))[1] == 3000
    assert idx.latest_at_or_before(target, T("2025-12-31T23:59:00")) is None     # nothing that early
    assert idx.latest_at_or_before(T("2026-01-05T12:00:00"), target) is None     # unknown target


def test_decision_cutoff_uses_uk_local_time():
    # January (GMT): 09:20 UK = 09:20 UTC on the previous day
    assert decision_cutoff(T("2026-01-15T12:00:00"), "09:20") == T("2026-01-14T09:20:00")
    assert decision_cutoff(T("2026-01-15T00:00:00"), "09:20") == T("2026-01-14T09:20:00")
    # July (BST): 09:20 UK = 08:20 UTC
    assert decision_cutoff(T("2026-07-15T12:00:00"), "09:20") == T("2026-07-14T08:20:00")
    # 23:30 UTC on 15 July is 00:30 BST on 16 July, so the delivery day is the 16th
    assert decision_cutoff(T("2026-07-15T23:30:00"), "09:20") == T("2026-07-15T08:20:00")


def test_decision_mode_uses_one_run_per_delivery_day():
    runs = ["2026-01-01T07:30:00Z", "2026-01-01T09:30:00Z", "2026-01-02T00:00:00Z"]
    targets = ["2026-01-02T06:00:00Z", "2026-01-02T20:00:00Z"]
    forecasts = [{"publishTime": p, "startTime": t, "generation": 1000 + i}
                 for t in targets for i, p in enumerate(runs)]
    actuals = [{"startTime": t, "generation": 1500} for t in targets]
    idx = ForecastIndex(forecasts)
    day = (T("2026-01-02T00:00:00"), T("2026-01-03T00:00:00"))

    rows = build_series(actuals, idx, *day, 12, gate_closure="09:20")
    assert [r["publishTime"] for r in rows] == ["2026-01-01T07:30:00Z"] * 2   # 09:30 run is after gate closure
    assert [r["leadHours"] for r in rows] == [22.5, 36.5]

    # fixed horizon picks a different run per hour for the same targets
    rows = build_series(actuals, idx, *day, 12)
    assert [r["publishTime"] for r in rows] == ["2026-01-01T09:30:00Z", "2026-01-02T00:00:00Z"]


def test_metrics_gate_closure_validation():
    client = TestClient(app)
    assert client.get("/api/metrics", params={"gate_closure": "9:2"}).status_code == 422
    res = client.get("/api/metrics", params={"gate_closure": "11:00"})
    assert res.status_code == 200
    assert res.json()["count"] > 0
