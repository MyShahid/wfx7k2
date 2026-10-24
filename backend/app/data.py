"""Loads the saved Elexon data once and keeps it in memory."""
import json
from functools import lru_cache
from pathlib import Path

from .analysis import ForecastIndex

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load():
    actuals = json.loads((DATA_DIR / "actuals.json").read_text())
    forecasts = json.loads((DATA_DIR / "forecasts.json").read_text())
    return actuals, ForecastIndex(forecasts), len(forecasts)
