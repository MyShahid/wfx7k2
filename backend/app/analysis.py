"""Core analysis: pick the forecast a trader would actually have had, and
measure how accurate it was. Pure functions, no web framework, easy to test.

Key rule (forecast horizon H):
    For a target time T, use the LATEST forecast whose publishTime <= T - H.
    That is the newest forecast available H hours before delivery.

Error convention:
    error = actual - forecast
    error < 0  -> wind came in BELOW forecast (shortfall, risky for the buyer)
    error > 0  -> wind came in ABOVE forecast (surplus)
"""
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt

# Beyond ~43h some January target hours have no forecast, so cap the horizon
# here to keep every horizon averaged over the same set of hours.
MAX_HORIZON_HOURS = 40


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class ForecastIndex:
    """For each target time, the forecast runs sorted by publish time."""

    def __init__(self, forecasts: list[dict]):
        runs: dict[datetime, list[tuple[datetime, float]]] = defaultdict(list)
        for f in forecasts:
            runs[parse_time(f["startTime"])].append((parse_time(f["publishTime"]), f["generation"]))
        self._runs = {t: sorted(v) for t, v in runs.items()}
        self._pub_times = {t: [p for p, _ in v] for t, v in self._runs.items()}

    def latest_before(self, target: datetime, horizon_hours: float):
        """Latest forecast for `target` published at least `horizon_hours` earlier."""
        pubs = self._pub_times.get(target)
        if not pubs:
            return None
        cutoff = target - timedelta(hours=horizon_hours)
        i = bisect_right(pubs, cutoff)          # pubs[:i] are all <= cutoff
        if i == 0:
            return None
        publish_time, generation = self._runs[target][i - 1]
        return publish_time, generation


def build_series(actuals: list[dict], index: ForecastIndex,
                 start: datetime, end: datetime, horizon_hours: float) -> list[dict]:
    """Actual vs selected forecast for every target time in [start, end)."""
    rows = []
    for a in actuals:
        t = parse_time(a["startTime"])
        if not (start <= t < end):
            continue
        f = index.latest_before(t, horizon_hours)
        row = {"time": iso(t), "actual": a["generation"],
               "forecast": None, "publishTime": None, "leadHours": None, "error": None}
        if f:
            publish_time, gen = f
            row.update(forecast=gen, publishTime=iso(publish_time),
                       leadHours=round((t - publish_time).total_seconds() / 3600, 1),
                       error=a["generation"] - gen)
        rows.append(row)
    return rows


def percentile(values: list[float], p: float) -> float:
    """Linear-interpolated percentile, p in [0, 100]."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def compute_metrics(rows: list[dict]) -> dict:
    """Accuracy statistics over rows that have both an actual and a forecast."""
    pairs = [r for r in rows if r["error"] is not None]
    n = len(pairs)
    if n == 0:
        return {"count": 0}
    errors = [r["error"] for r in pairs]
    abs_err = [abs(e) for e in errors]
    actual_mean = sum(r["actual"] for r in pairs) / n
    mae = sum(abs_err) / n

    by_hour = defaultdict(list)
    for r in pairs:
        by_hour[parse_time(r["time"]).hour].append(abs(r["error"]))

    return {
        "count": n,
        "mae": round(mae),
        "rmse": round(sqrt(sum(e * e for e in errors) / n)),
        "bias": round(sum(errors) / n),                      # mean(actual - forecast)
        "nmae_pct": round(100 * mae / actual_mean, 1) if actual_mean else None,
        "actual_mean": round(actual_mean),
        "error_p10": round(percentile(errors, 10)),
        "error_p50": round(percentile(errors, 50)),
        "error_p90": round(percentile(errors, 90)),
        "abs_error_p90": round(percentile(abs_err, 90)),
        "max_shortfall": round(min(errors)),                  # worst over-forecast
        "max_surplus": round(max(errors)),
        "mae_by_hour": [{"hour": h, "mae": round(sum(v) / len(v))} for h, v in sorted(by_hour.items())],
        "error_histogram": histogram(errors, bin_size=1000),
    }


def histogram(values: list[float], bin_size: int) -> list[dict]:
    counts = defaultdict(int)
    for v in values:
        counts[int(v // bin_size) * bin_size] += 1
    return [{"from": k, "to": k + bin_size, "count": counts[k]} for k in sorted(counts)]


def horizon_curve(actuals: list[dict], index: ForecastIndex, start: datetime, end: datetime,
                  horizons=range(0, MAX_HORIZON_HOURS + 1, 2)) -> list[dict]:
    """How accuracy changes as forecasts are made further ahead."""
    out = []
    for h in horizons:
        m = compute_metrics(build_series(actuals, index, start, end, h))
        if m["count"]:
            out.append({"horizon": h, "mae": m["mae"], "rmse": m["rmse"],
                        "bias": m["bias"], "error_p10": m["error_p10"], "count": m["count"]})
    return out
