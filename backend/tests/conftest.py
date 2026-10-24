import json

import pytest
from fastapi.testclient import TestClient

from app.data import DATA_DIR
from app.main import app

ACTUALS_FILE = DATA_DIR / "actuals.json"
FORECASTS_FILE = DATA_DIR / "forecasts.json"


def _require_data():
    if not (ACTUALS_FILE.exists() and FORECASTS_FILE.exists()):
        pytest.skip("backend/data/actuals.json and forecasts.json are not present")


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def real_data():
    """(actuals, ForecastIndex, forecast row count) from backend/data, as the API loads it."""
    _require_data()
    from app.data import load
    return load()


@pytest.fixture(scope="session")
def raw_forecasts():
    """The forecast rows exactly as stored in forecasts.json."""
    _require_data()
    return json.loads(FORECASTS_FILE.read_text())
