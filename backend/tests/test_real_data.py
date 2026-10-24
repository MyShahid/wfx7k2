"""Checks against the saved January 2026 Elexon data. Skipped if backend/data is missing."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pytest

from app.analysis import UK, build_series, compute_metrics, parse_time

JANUARY = (datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc))
ON_THE_HOUR_HOURS = 31 * 24


@pytest.mark.parametrize("horizon", range(0, 41))
def test_every_january_hour_has_a_forecast(real_data, horizon):
    actuals, index, _ = real_data
    rows = build_series(actuals, index, *JANUARY, horizon)
    on_hour = [r for r in rows if r["time"].endswith(":00:00Z")]
    assert len(on_hour) == ON_THE_HOUR_HOURS
    assert all(r["forecast"] is not None for r in on_hour)
    assert compute_metrics(rows)["count"] == ON_THE_HOUR_HOURS


def test_selection_matches_brute_force(real_data, raw_forecasts):
    actuals, index, _ = real_data
    runs_by_target = defaultdict(list)
    for f in raw_forecasts:
        runs_by_target[f["startTime"]].append(f)

    checked = 0
    for horizon in (0, 0.5, 1.5, 6, 13, 24, 33.5, 40):
        rows = build_series(actuals, index, *JANUARY, horizon)
        for r in rows[::7]:                                     # every 7th half-hour: a spread of hours
            cutoff = parse_time(r["time"]) - timedelta(hours=horizon)
            candidates = [f for f in runs_by_target.get(r["time"], []) if parse_time(f["publishTime"]) <= cutoff]
            if not candidates:
                assert r["forecast"] is None
                continue
            best = max(candidates, key=lambda f: parse_time(f["publishTime"]))
            assert r["publishTime"] == best["publishTime"]
            assert r["forecast"] == best["generation"]
            assert r["leadHours"] >= horizon
            checked += 1
    assert checked > 500


def test_decision_time_uses_one_run_per_delivery_day(real_data):
    actuals, index, _ = real_data
    rows = build_series(actuals, index, *JANUARY, 0, gate_closure="09:20")
    matched = [r for r in rows if r["forecast"] is not None]
    assert len(matched) == ON_THE_HOUR_HOURS

    runs_per_day = defaultdict(set)
    for r in matched:
        runs_per_day[parse_time(r["time"]).astimezone(UK).date()].add(r["publishTime"])
    assert len(runs_per_day) == 31
    assert all(len(runs) == 1 for runs in runs_per_day.values())
    # each day's run was published at or before 09:20 UK on the day before
    for day, (run,) in runs_per_day.items():
        cutoff = datetime.combine(day - timedelta(days=1), datetime.min.time(), tzinfo=UK) + timedelta(hours=9, minutes=20)
        assert parse_time(run) <= cutoff


# Values already reported for January 2026; a change here means the analysis changed.
@pytest.mark.parametrize("kwargs, mae, bias", [
    ({"horizon_hours": 24}, 2050, -1854),
    ({"horizon_hours": 0, "gate_closure": "09:20"}, 2127, -1852),
])
def test_regression_values(real_data, kwargs, mae, bias):
    actuals, index, _ = real_data
    m = compute_metrics(build_series(actuals, index, *JANUARY, **kwargs))
    assert m["count"] == ON_THE_HOUR_HOURS
    assert (m["mae"], m["bias"]) == (mae, bias)
