"""FastAPI app. All routes live under /api so the same code runs locally,
in Docker and as a Vercel serverless function."""
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .analysis import MAX_HORIZON_HOURS, build_series, compute_metrics, horizon_curve
from .data import load

DATA_FIRST_DAY = date(2026, 1, 1)
DATA_LAST_DAY = date(2026, 1, 31)

# Day-ahead auction gate closure on D-1, UK local time. This is a configurable
# assumption: confirm the actual time with the client's trading desk.
DEFAULT_GATE_CLOSURE = "09:20"
GATE_CLOSURE_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"

app = FastAPI(title="UK Wind Forecast Monitor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def to_range(start: date, end: date) -> tuple[datetime, datetime]:
    """Validate dates and turn [start, end] days into a UTC [from, to) window."""
    if start > end:
        raise HTTPException(400, "start must be on or before end")
    if start < DATA_FIRST_DAY or end > DATA_LAST_DAY:
        raise HTTPException(400, f"dates must be between {DATA_FIRST_DAY} and {DATA_LAST_DAY}")
    return (datetime.combine(start, time.min, tzinfo=timezone.utc),
            datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc))


@app.get("/api/health")
def health():
    actuals, _, n_forecasts = load()
    return {"status": "ok", "actuals": len(actuals), "forecast_rows": n_forecasts}


@app.get("/api/meta")
def meta():
    return {"first_day": DATA_FIRST_DAY, "last_day": DATA_LAST_DAY,
            "default_horizon": 24, "max_horizon": MAX_HORIZON_HOURS,
            "default_gate_closure": DEFAULT_GATE_CLOSURE, "unit": "MW"}


@app.get("/api/series")
def series(start: date = Query(DATA_FIRST_DAY), end: date = Query(DATA_LAST_DAY),
           horizon: float = Query(24, ge=0, le=MAX_HORIZON_HOURS),
           gate_closure: str | None = Query(None, pattern=GATE_CLOSURE_PATTERN)):
    """Actual wind generation vs the forecast available at gate closure on the
    day before (if `gate_closure` is given) or `horizon` hours earlier."""
    frm, to = to_range(start, end)
    actuals, index, _ = load()
    return build_series(actuals, index, frm, to, horizon, gate_closure)


@app.get("/api/metrics")
def metrics(start: date = Query(DATA_FIRST_DAY), end: date = Query(DATA_LAST_DAY),
            horizon: float = Query(24, ge=0, le=MAX_HORIZON_HOURS),
            gate_closure: str | None = Query(None, pattern=GATE_CLOSURE_PATTERN)):
    """Accuracy statistics for the chosen period and gate closure or horizon."""
    frm, to = to_range(start, end)
    actuals, index, _ = load()
    return compute_metrics(build_series(actuals, index, frm, to, horizon, gate_closure))


@app.get("/api/horizon-curve")
def horizon(start: date = Query(DATA_FIRST_DAY), end: date = Query(DATA_LAST_DAY)):
    """Forecast error at horizons 0..40h, to show how accuracy drops with lead time."""
    frm, to = to_range(start, end)
    actuals, index, _ = load()
    return horizon_curve(actuals, index, frm, to)


# In Docker, the built React app is served by FastAPI from the same port.
# (Mounted last so the /api routes above take priority.)
_static = os.environ.get("STATIC_DIR")
if _static and Path(_static).is_dir():
    app.mount("/", StaticFiles(directory=_static, html=True), name="frontend")
