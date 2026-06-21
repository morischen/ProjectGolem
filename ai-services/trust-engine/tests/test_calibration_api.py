"""Trust Engine calibration ledger: record a benchmark run, list history (§28.12)."""

from eip_persistence import InMemoryCalibrationStore
from fastapi.testclient import TestClient

from eip_trust.api import create_app


def _client() -> TestClient:
    return TestClient(create_app(calibration_store=InMemoryCalibrationStore()))


def test_ledger_starts_empty():
    assert _client().get("/v1/calibration/runs").json() == []


def test_record_run_appends_a_benchmark_snapshot():
    client = _client()
    res = client.post("/v1/calibration/runs")
    assert res.status_code == 200
    run = res.json()
    assert run["id"] == 1
    # The seed set is golden -> perfect verdict accuracy.
    assert run["verdict_accuracy"] == 1.0
    assert run["total"] >= 1
    assert "by_difficulty" in run["payload"]


def test_runs_accumulate_newest_first():
    client = _client()
    client.post("/v1/calibration/runs")
    client.post("/v1/calibration/runs")
    runs = client.get("/v1/calibration/runs").json()
    assert [r["id"] for r in runs] == [2, 1]
