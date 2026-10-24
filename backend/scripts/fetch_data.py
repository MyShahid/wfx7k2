"""Download January 2026 wind data from Elexon BMRS and save it as JSON.

Run once (from the backend folder):  python scripts/fetch_data.py

- Actuals  (FUELHH, fuelType=WIND): half-hourly generation for 1-31 Jan 2026
- Forecasts (WINDFOR): every forecast run published from 29 Dec 2025 up to
  31 Jan 2026, so that every January target hour has its day-ahead forecasts.
"""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TARGET_START = date(2026, 1, 1)
TARGET_END = date(2026, 1, 31)          # inclusive
FORECAST_LOOKBACK_DAYS = 3              # forecasts reach ~2 days ahead


def fetch_actuals(client: httpx.Client) -> list[dict]:
    rows = {}
    day = TARGET_START
    while day <= TARGET_END:
        chunk_end = min(day + timedelta(days=6), TARGET_END)
        r = client.get(f"{BASE}/FUELHH/stream", params={
            "settlementDateFrom": day.isoformat(),
            "settlementDateTo": chunk_end.isoformat(),
            "fuelType": "WIND",
        })
        r.raise_for_status()
        for rec in r.json():
            if rec.get("fuelType") != "WIND":
                continue
            key = rec["startTime"]
            # If a period was re-published, keep the most recent version
            if key not in rows or rec["publishTime"] > rows[key]["publishTime"]:
                rows[key] = {"startTime": rec["startTime"],
                             "publishTime": rec["publishTime"],
                             "generation": rec["generation"]}
        print(f"actuals  {day} .. {chunk_end}: total {len(rows)}")
        day = chunk_end + timedelta(days=1)
    return sorted(rows.values(), key=lambda x: x["startTime"])


def fetch_forecasts(client: httpx.Client) -> list[dict]:
    rows = {}
    start = datetime.combine(TARGET_START - timedelta(days=FORECAST_LOOKBACK_DAYS),
                             datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(TARGET_END + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=1), end)
        r = client.get(f"{BASE}/WINDFOR/stream", params={
            "publishDateTimeFrom": cur.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": nxt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        r.raise_for_status()
        for rec in r.json():
            key = (rec["publishTime"], rec["startTime"])
            rows[key] = {"publishTime": rec["publishTime"],
                         "startTime": rec["startTime"],
                         "generation": rec["generation"]}
        print(f"forecasts {cur:%Y-%m-%d}: total {len(rows)}")
        cur = nxt
    return sorted(rows.values(), key=lambda x: (x["startTime"], x["publishTime"]))


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with httpx.Client(timeout=60) as client:
        actuals = fetch_actuals(client)
        forecasts = fetch_forecasts(client)
    (DATA_DIR / "actuals.json").write_text(json.dumps(actuals))
    (DATA_DIR / "forecasts.json").write_text(json.dumps(forecasts))
    print(f"Saved {len(actuals)} actuals and {len(forecasts)} forecast rows to {DATA_DIR}")


if __name__ == "__main__":
    main()
