"""Comprehensive unit and integration test suite for the FastAPI internal maritime daemon (Stage B)."""

import os
from pathlib import Path
import warnings
import pytest

try:
    from starlette.exceptions import StarletteDeprecationWarning
except ImportError:
    try:
        from starlette.warnings import StarletteDeprecationWarning
    except ImportError:
        StarletteDeprecationWarning = DeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=StarletteDeprecationWarning,
        message=r".*Using `httpx` with `starlette.testclient` is deprecated.*",
    )
    from fastapi.testclient import TestClient

from src.simulation.daemon import app, container, run_daemon


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient triggering FastAPI lifespan setup."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint_healthy(client):
    """Verifies that /internal/v1/health returns 200 with complete model provenance and weights SHA-256."""
    resp = client.get("/internal/v1/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "HEALTHY"
    assert data["model_loaded"] is True
    assert data["model_name"] == "VectorizedRidgeETAModel"
    assert data["model_alpha"] == 10.0
    assert len(data["model_weights_sha256"]) == 64
    assert data["active_vessels_count"] == 4
    assert data["timestamp_utc"].endswith("Z")


def test_status_endpoint_returns_simulation_state(client):
    """Verifies that /internal/v1/status returns active simulation clock and counters."""
    resp = client.get("/internal/v1/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["simulation_available"] is True
    assert data["is_running"] is False
    assert data["is_paused"] is False
    assert "2026-03-01" in data["sim_time_utc"]
    assert data["speed_multiplier"] == 1.0
    assert data["active_vessels_count"] == 4
    assert data["total_events_generated"] >= 4
    assert data["provenance"] == "SIMULATED_LOCAL_MARITIME_ENGINE"


def test_fleet_snapshot_endpoint_integrity(client):
    """Verifies that /internal/v1/fleet/snapshot returns dynamic coordinates and valid ETA states."""
    resp = client.get("/internal/v1/fleet/snapshot")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_vessels"] == 4
    assert len(data["vessels"]) == 4

    for v in data["vessels"]:
        assert v["vessel_id"] in [
            "V-FROMVEUR-SIM",
            "V-AZENOR-SIM",
            "V-OUESSANT-SIM",
            "V-SEIN-SIM",
        ]
        assert v["name"] in [
            "SIM_FROMVEUR_EXPRESS",
            "SIM_AZENOR_VOYAGER",
            "SIM_IROISE_STAR",
            "SIM_SEIN_SHUTTLE",
        ]

        assert 47.9 <= v["lat"] <= 48.6
        assert -5.2 <= v["lon"] <= -4.3
        assert v["sog_knots"] >= 0.0
        assert v["data_provenance"] == "SIMULATED_SYNTHETIC"
        assert v["position_timestamp_utc"].endswith("Z")
        assert v["eta_lifecycle_state"] in [
            "SCHEDULED",
            "ESTIMATING",
            "IN_TRANSIT",
            "APPROACHING",
            "ARRIVED",
            "STALE_DATA",
            "DELAYED_OR_UNCERTAIN",
        ]


def test_single_vessel_eta_provenance(client):
    """Verifies that /internal/v1/vessels/{id}/eta returns deep prediction provenance and timestamps."""
    resp = client.get("/internal/v1/vessels/SIM_FROMVEUR_EXPRESS/eta")
    assert resp.status_code == 200
    data = resp.json()

    assert data["schema_version"] == "1.0.0"
    assert data["vessel_id"] == "V-FROMVEUR-SIM"
    assert data["vessel_name"] == "SIM_FROMVEUR_EXPRESS"
    assert data["synthetic_mmsi"] == 999000001
    assert data["corridor"] == "BREST_LE_CONQUET"

    # Provenance fields
    prov = data["provenance"]
    assert prov["is_synthetic"] is True
    assert prov["model_name"] == "VectorizedRidgeETAModel"
    assert prov["prediction_source"] == "ML_MODEL_INFERENCE"
    assert len(prov["weight_checksum_sha256"]) == 64

    # Timestamp fields
    ts = data["timestamps"]
    assert "position_timestamp_utc" in ts
    assert "predicted_arrival_utc" in ts
    assert ts["telemetry_age_seconds"] >= 0.0

    # Predictions
    preds = data["predictions"]
    assert preds["displayed_remaining_minutes"] > 0.0
    assert preds["raw_model_remaining_minutes"] > 0.0


def test_vessel_not_found_returns_404(client):
    """Verifies that querying a non-existent vessel ID returns HTTP 404."""
    resp = client.get("/internal/v1/vessels/NON_EXISTENT_VESSEL_999/eta")
    assert resp.status_code == 404
    assert "not found in active simulation" in resp.json()["detail"]


def test_simulation_controls_lifecycle(client):
    """Verifies that control actions (pause, resume, speed, reset) measurably affect the runner."""
    # 1. Pause
    resp_pause = client.post("/internal/v1/simulation/control", json={"action": "pause"})
    assert resp_pause.status_code == 200
    assert resp_pause.json()["is_paused"] is True
    assert client.get("/internal/v1/status").json()["is_paused"] is True

    # 2. Resume
    resp_resume = client.post("/internal/v1/simulation/control", json={"action": "resume"})
    assert resp_resume.status_code == 200
    assert resp_resume.json()["is_paused"] is False
    assert client.get("/internal/v1/status").json()["is_paused"] is False

    # 3. Speed Multiplier
    resp_speed = client.post(
        "/internal/v1/simulation/control",
        json={"action": "speed", "speed_multiplier": 5.0},
    )
    assert resp_speed.status_code == 200
    assert resp_speed.json()["speed_multiplier"] == 5.0
    assert client.get("/internal/v1/status").json()["speed_multiplier"] == 5.0

    # 4. Reset
    resp_reset = client.post("/internal/v1/simulation/control", json={"action": "reset"})
    assert resp_reset.status_code == 200
    assert "reset to initial dock state" in resp_reset.json()["message"]


def test_simulation_controls_validation_errors(client):
    """Verifies that invalid actions or invalid speed multipliers return HTTP 422."""
    # Invalid action
    resp_invalid_action = client.post("/internal/v1/simulation/control", json={"action": "destroy"})
    assert resp_invalid_action.status_code == 422

    # Negative speed multiplier
    resp_neg_speed = client.post(
        "/internal/v1/simulation/control",
        json={"action": "speed", "speed_multiplier": -2.0},
    )
    assert resp_neg_speed.status_code == 422

    # Speed multiplier exceeding 100.0
    resp_huge_speed = client.post(
        "/internal/v1/simulation/control",
        json={"action": "speed", "speed_multiplier": 500.0},
    )
    assert resp_huge_speed.status_code == 422


def test_scenario_activation(client):
    """Verifies triggering an existing scenario activates it and updates runner state."""
    resp = client.post("/internal/v1/simulation/scenarios/scenario-1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPLIED"
    assert resp.json()["scenario_id"] == "SCENARIO_01_NORMAL_VOYAGE"

    status_data = client.get("/internal/v1/status").json()
    assert status_data["active_scenario_id"] == "SCENARIO_01_NORMAL_VOYAGE"


def test_invalid_scenario_returns_404(client):
    """Verifies triggering an unknown scenario returns HTTP 404."""
    resp = client.post("/internal/v1/simulation/scenarios/non_existent_scenario_xyz")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_loopback_security_enforcement():
    """Verifies that run_daemon raises ValueError if an attempt is made to bind beyond loopback."""
    with pytest.raises(ValueError) as exc_info:
        run_daemon(host="0.0.0.0", port=8000)
    assert "SECURITY VIOLATION" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        run_daemon(host="192.168.1.100", port=8000)
    assert "SECURITY VIOLATION" in str(exc_info.value)


def test_unavailable_model_returns_honest_503(monkeypatch):
    """Verifies that if model fails to load, endpoints return HTTP 503 instead of fabricated ETAs."""
    # Temporarily set fault injection environment flag
    monkeypatch.setenv("SIMULATION_FORCE_MODEL_FAILURE", "1")
    container.initialize()

    with TestClient(app) as fail_client:
        # Health returns 503
        resp_health = fail_client.get("/internal/v1/health")
        assert resp_health.status_code == 503
        assert resp_health.json()["model_loaded"] is False

        # Status returns 503
        resp_status = fail_client.get("/internal/v1/status")
        assert resp_status.status_code == 503

        # Fleet snapshot returns 503 (NOT fabricated mock data!)
        resp_fleet = fail_client.get("/internal/v1/fleet/snapshot")
        assert resp_fleet.status_code == 503

    # Restore container
    monkeypatch.delenv("SIMULATION_FORCE_MODEL_FAILURE", raising=False)
    container.initialize()
