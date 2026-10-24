from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.analysis import (MAX_HORIZON_HOURS, ForecastIndex, build_series, compute_metrics,
                          horizon_curve, percentile)
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
