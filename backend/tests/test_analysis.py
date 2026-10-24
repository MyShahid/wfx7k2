from datetime import datetime, timezone

import pytest

from app.analysis import (MAX_HORIZON_HOURS, ForecastIndex, build_series, compute_metrics,
                          decision_cutoff, histogram, horizon_curve, percentile)

T = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

FORECASTS = [
    # three forecast runs for the same target hour 2026-01-02 12:00
    {"publishTime": "2026-01-01T00:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 1000},
    {"publishTime": "2026-01-01T12:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 2000},
    {"publishTime": "2026-01-02T06:00:00Z", "startTime": "2026-01-02T12:00:00Z", "generation": 3000},
]
ACTUALS = [{"startTime": "2026-01-02T12:00:00Z", "generation": 2500}]
JAN_2 = (T("2026-01-02T00:00:00"), T("2026-01-03T00:00:00"))


def fc(publish, start, generation=1000):
    return {"publishTime": publish, "startTime": start, "generation": generation}


# ---- forecast selection -------------------------------------------------------

def test_picks_latest_forecast_published_before_horizon():
    idx = ForecastIndex(FORECASTS)
    target = T("2026-01-02T12:00:00")
    assert idx.latest_before(target, 4)[1] == 3000    # 06:00 run is 6h before
    assert idx.latest_before(target, 12)[1] == 2000   # 06:00 too late, 12:00 prev day ok
    assert idx.latest_before(target, 24)[1] == 2000   # exactly 24h before counts
    assert idx.latest_before(target, 30)[1] == 1000
    assert idx.latest_before(target, 48) is None      # nothing published that early


def test_latest_at_or_before():
    idx = ForecastIndex(FORECASTS)
    target = T("2026-01-02T12:00:00")
    assert idx.latest_at_or_before(target, T("2026-01-01T12:00:00"))[1] == 2000   # exactly at cutoff counts
    assert idx.latest_at_or_before(target, T("2026-01-01T11:59:00"))[1] == 1000
    assert idx.latest_at_or_before(target, T("2026-01-03T00:00:00"))[1] == 3000
    assert idx.latest_at_or_before(target, T("2025-12-31T23:59:00")) is None     # nothing that early
    assert idx.latest_at_or_before(T("2026-01-05T12:00:00"), target) is None     # unknown target


def test_half_hour_actuals_get_no_forecast_and_are_excluded_from_metrics():
    actuals = [{"startTime": "2026-01-02T12:00:00Z", "generation": 2500},
               {"startTime": "2026-01-02T12:30:00Z", "generation": 9999}]
    rows = build_series(actuals, ForecastIndex(FORECASTS), *JAN_2, 24)
    assert [r["time"] for r in rows] == ["2026-01-02T12:00:00Z", "2026-01-02T12:30:00Z"]
    half = rows[1]
    assert half["forecast"] is None and half["error"] is None
    assert half["publishTime"] is None and half["leadHours"] is None
    m = compute_metrics(rows)
    assert m["count"] == 1
    assert m["actual_mean"] == 2500                   # the 12:30 actual is not averaged in


def test_forecasts_published_after_target_are_never_selected():
    target = "2026-01-02T12:00:00Z"
    idx = ForecastIndex([fc("2026-01-02T11:00:00Z", target, 1100),
                         fc("2026-01-02T12:00:01Z", target, 9999),     # 1 s after the target
                         fc("2026-01-02T15:00:00Z", target, 9999)])    # negative lead
    rows = build_series([{"startTime": target, "generation": 1000}], idx, *JAN_2, 0)
    assert rows[0]["forecast"] == 1100
    assert rows[0]["leadHours"] == 1.0

    only_late = ForecastIndex([fc("2026-01-02T13:00:00Z", target)])
    assert only_late.latest_before(T("2026-01-02T12:00:00"), 0) is None
    rows = build_series([{"startTime": target, "generation": 1000}], only_late, *JAN_2, 0)
    assert rows[0]["forecast"] is None


def test_fractional_horizon():
    target = "2026-01-02T12:00:00Z"
    idx = ForecastIndex([fc("2026-01-02T10:00:00Z", target, 1000),
                         fc("2026-01-02T10:30:00Z", target, 1030),
                         fc("2026-01-02T11:00:00Z", target, 1100)])
    t = T("2026-01-02T12:00:00")
    assert idx.latest_before(t, 1.5)[1] == 1030       # cutoff 10:30 exactly
    assert idx.latest_before(t, 1.6)[1] == 1000       # cutoff 10:24
    assert idx.latest_before(t, 0.5)[1] == 1100
    rows = build_series([{"startTime": target, "generation": 1000}], idx, *JAN_2, 1.5)
    assert rows[0]["leadHours"] == 1.5


def test_target_without_any_forecast():
    rows = build_series([{"startTime": "2026-01-02T15:00:00Z", "generation": 1000}],
                        ForecastIndex(FORECASTS), *JAN_2, 0)
    assert len(rows) == 1
    assert rows[0]["forecast"] is None and rows[0]["error"] is None
    assert compute_metrics(rows) == {"count": 0}


def test_build_series_window_includes_start_excludes_end():
    actuals = [{"startTime": s, "generation": 1} for s in
               ["2026-01-01T23:30:00Z", "2026-01-02T00:00:00Z", "2026-01-02T23:30:00Z", "2026-01-03T00:00:00Z"]]
    rows = build_series(actuals, ForecastIndex([]), *JAN_2, 24)
    assert [r["time"] for r in rows] == ["2026-01-02T00:00:00Z", "2026-01-02T23:30:00Z"]


def test_series_and_error_sign():
    rows = build_series(ACTUALS, ForecastIndex(FORECASTS), *JAN_2, 24)
    assert rows[0]["forecast"] == 2000
    assert rows[0]["error"] == 500                    # actual - forecast
    assert rows[0]["leadHours"] == 24.0


# ---- metrics ------------------------------------------------------------------

def test_metrics():
    rows = [{"time": "2026-01-02T00:00:00Z", "actual": 100, "forecast": 90, "error": 10},
            {"time": "2026-01-02T01:00:00Z", "actual": 100, "forecast": 130, "error": -30}]
    m = compute_metrics(rows)
    assert m["count"] == 2
    assert m["mae"] == 20
    assert m["bias"] == -10
    assert m["max_shortfall"] == -30


def test_metrics_with_no_matched_rows():
    assert compute_metrics([]) == {"count": 0}
    rows = [{"time": "2026-01-02T00:30:00Z", "actual": 100, "forecast": None, "error": None}]
    assert compute_metrics(rows) == {"count": 0}


def test_metrics_against_hand_calculated_values():
    # errors -500, -100, 100, 300 with every actual = 1000 MW; plus one unmatched row
    rows = [
        {"time": "2026-01-02T00:00:00Z", "actual": 1000, "forecast": 1500, "error": -500},
        {"time": "2026-01-02T00:00:00Z", "actual": 1000, "forecast": 1100, "error": -100},
        {"time": "2026-01-02T01:00:00Z", "actual": 1000, "forecast": 900, "error": 100},
        {"time": "2026-01-02T01:00:00Z", "actual": 1000, "forecast": 700, "error": 300},
        {"time": "2026-01-02T01:30:00Z", "actual": 5000, "forecast": None, "error": None},
    ]
    m = compute_metrics(rows)
    assert m["count"] == 4
    assert m["mae"] == 250                 # (500 + 100 + 100 + 300) / 4
    assert m["rmse"] == 300                # sqrt((250000 + 10000 + 10000 + 90000) / 4)
    assert m["bias"] == -50                # (-500 - 100 + 100 + 300) / 4
    assert m["actual_mean"] == 1000
    assert m["nmae_pct"] == 25.0           # 100 * 250 / 1000
    # sorted errors [-500, -100, 100, 300]; rank k = 3p/100, linear interpolation
    assert m["error_p10"] == -380          # k=0.3: -500 + 0.3 * 400
    assert m["error_p50"] == 0             # k=1.5: -100 + 0.5 * 200
    assert m["error_p90"] == 240           # k=2.7: 100 + 0.7 * 200
    assert m["abs_error_p90"] == 440       # sorted |e| [100, 100, 300, 500]; k=2.7: 300 + 0.7 * 200
    assert m["max_shortfall"] == -500
    assert m["max_surplus"] == 300
    assert m["mae_by_hour"] == [{"hour": 0, "mae": 300}, {"hour": 1, "mae": 200}]
    assert m["error_histogram"] == [{"from": -1000, "to": 0, "count": 2}, {"from": 0, "to": 1000, "count": 2}]


def test_histogram_bin_edges():
    bins = {b["from"]: b["count"] for b in histogram([-1, -1000, 0, 999, 1000, -1001], 1000)}
    assert bins == {-2000: 1, -1000: 2, 0: 2, 1000: 1}
    assert histogram([-1], 1000) == [{"from": -1000, "to": 0, "count": 1}]
    assert histogram([-1000], 1000) == [{"from": -1000, "to": 0, "count": 1}]
    assert histogram([0], 1000) == [{"from": 0, "to": 1000, "count": 1}]


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([0, 10], 10) == 1


@pytest.mark.parametrize("p", [0, 10, 50, 90, 100])
def test_percentile_single_value(p):
    assert percentile([42], p) == 42


def test_percentile_empty_list():
    assert percentile([], 50) == 0.0


# ---- horizon curve -----------------------------------------------------------

def test_horizon_curve_capped_at_max_horizon():
    # add a run 60h ahead so every horizon up to 48h would have data without the cap
    forecasts = FORECASTS + [{"publishTime": "2025-12-31T00:00:00Z",
                              "startTime": "2026-01-02T12:00:00Z", "generation": 500}]
    curve = horizon_curve(ACTUALS, ForecastIndex(forecasts), *JAN_2)
    assert MAX_HORIZON_HOURS == 40
    assert [c["horizon"] for c in curve] == list(range(0, 41, 2))


def test_horizon_curve_skips_empty_horizons_and_reports_count():
    targets = ["2026-01-02T12:00:00Z", "2026-01-02T13:00:00Z"]
    forecasts = [fc("2026-01-02T09:00:00Z", targets[0]),     # 3 h before 12:00
                 fc("2026-01-02T09:00:00Z", targets[1])]     # 4 h before 13:00
    actuals = [{"startTime": t, "generation": 1000} for t in targets]
    curve = horizon_curve(actuals, ForecastIndex(forecasts), *JAN_2)
    assert [(c["horizon"], c["count"]) for c in curve] == [(0, 2), (2, 2), (4, 1)]
    assert set(curve[0]) == {"horizon", "mae", "rmse", "bias", "error_p10", "count"}


# ---- decision time -------------------------------------------------------------

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

    rows = build_series(actuals, idx, *JAN_2, 12, gate_closure="09:20")
    assert [r["publishTime"] for r in rows] == ["2026-01-01T07:30:00Z"] * 2   # 09:30 run is after gate closure
    assert [r["leadHours"] for r in rows] == [22.5, 36.5]

    # fixed horizon picks a different run per hour for the same targets
    rows = build_series(actuals, idx, *JAN_2, 12)
    assert [r["publishTime"] for r in rows] == ["2026-01-01T09:30:00Z", "2026-01-02T00:00:00Z"]


def _full_day(runs):
    targets = [f"2026-01-02T{h:02d}:00:00Z" for h in range(24)]
    forecasts = [fc(p, t) for t in targets for p in runs]
    actuals = [{"startTime": t, "generation": 1000} for t in targets]
    return actuals, ForecastIndex(forecasts)


def test_decision_mode_run_exactly_at_gate_closure_counts():
    actuals, idx = _full_day(["2026-01-01T07:30:00Z", "2026-01-01T09:20:00Z", "2026-01-01T09:21:00Z"])
    rows = build_series(actuals, idx, *JAN_2, 0, gate_closure="09:20")
    assert len(rows) == 24
    assert {r["publishTime"] for r in rows} == {"2026-01-01T09:20:00Z"}   # not the 09:21 run


def test_decision_mode_run_one_minute_after_gate_closure_does_not_count():
    actuals, idx = _full_day(["2026-01-01T07:30:00Z", "2026-01-01T09:21:00Z"])
    rows = build_series(actuals, idx, *JAN_2, 0, gate_closure="09:20")
    assert {r["publishTime"] for r in rows} == {"2026-01-01T07:30:00Z"}


def test_decision_mode_ignores_horizon():
    actuals, idx = _full_day(["2026-01-01T07:30:00Z"])
    for h in (0, 24, 40):
        rows = build_series(actuals, idx, *JAN_2, h, gate_closure="09:20")
        assert all(r["publishTime"] == "2026-01-01T07:30:00Z" for r in rows)
