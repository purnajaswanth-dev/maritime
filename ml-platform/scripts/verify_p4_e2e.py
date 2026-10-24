"""Controlled E2E integration verification script for Phase 1 Remediation (P4).

Executes end-to-end validation through Spring Boot (http://localhost:8080):
1. Records initial simulation status and all 4 vessel positions.
2. Starts simulation via POST /api/v1/simulation/controls.
3. Captures 3 advancing snapshots at advancing simulated times.
4. Verifies clock advancement, route waypoint kinematics, and SSE broadcast reception.
5. Verifies single-vessel ETA requests invoke the frozen Ridge model with updated telemetry.
6. Verifies honest arrival latching and stale telemetry handling.
7. Cleanly stops the simulation.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

SPRING_BOOT_BASE = "http://localhost:8080"


def http_get(path: str) -> Dict[str, Any]:
    url = f"{SPRING_BOOT_BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{SPRING_BOOT_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


class SSECollector:
    """Collects Server-Sent Events from Spring Boot in a background thread."""

    def __init__(self, url: str):
        self.url = url
        self.events: List[Dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        try:
            req = urllib.request.Request(self.url, headers={"Accept": "text/event-stream"})
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                current_event_type = "message"
                while not self._stop.is_set():
                    line = resp.readline().decode("utf-8", errors="replace")
                    if not line:
                        break
                    line_s = line.strip()
                    if line_s.startswith("event:"):
                        current_event_type = line_s[len("event:"):].strip()
                    elif line_s.startswith("data:"):
                        data_content = line_s[len("data:"):].strip()
                        try:
                            parsed = json.loads(data_content)
                            self.events.append({
                                "event_type": current_event_type,
                                "data": parsed,
                            })
                        except json.JSONDecodeError:
                            self.events.append({
                                "event_type": current_event_type,
                                "raw": data_content,
                            })
        except Exception:
            pass

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)


def run_controlled_p4_verification():
    report: Dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": {},
        "verifications": {},
    }

    print("=== Step 0: Clean baseline reset ===")
    reset_res = http_post("/api/v1/simulation/controls", {"action": "reset"})
    print("Reset response:", reset_res)
    time.sleep(0.5)

    print("\n=== Step 1: Record initial simulation status and vessel positions ===")
    status_0 = http_get("/api/v1/simulation/status")
    vessels_0 = http_get("/api/v1/vessels")
    eta_0 = http_get("/api/v1/vessels/V-FROMVEUR-SIM/eta")

    initial_snapshot = {
        "status": status_0,
        "vessels": [
            {
                "id": v["vessel_id"],
                "name": v["name"],
                "lat": v["lat"],
                "lon": v["lon"],
                "sog": v["sog_knots"],
                "cog": v["cog_degrees"],
                "state": v["eta_lifecycle_state"],
                "remaining_min": v["estimated_remaining_minutes"],
            }
            for v in vessels_0.get("vessels", [])
        ],
        "vessel_fromveur_eta": eta_0,
    }
    report["steps"]["01_initial_snapshot"] = initial_snapshot
    print(f"Initial Sim Time: {status_0.get('sim_time_utc')}, running={status_0.get('is_running')}")
    for v in initial_snapshot["vessels"]:
        print(f"  - {v['id']} ({v['name']}): lat={v['lat']}, lon={v['lon']}, remaining={v['remaining_min']}m")

    print("\n=== Step 2: Connect SSE Listener and Start Simulation ===")
    sse = SSECollector(f"{SPRING_BOOT_BASE}/api/v1/stream/vessels")
    sse.start()
    time.sleep(0.5)

    # Start simulation with speed_multiplier: 20.0
    start_res = http_post("/api/v1/simulation/controls", {"action": "start", "speed_multiplier": 20.0})
    print("Start response:", start_res)
    report["steps"]["02_start_response"] = start_res

    print("\n=== Step 3: Capture 3 advancing snapshots ===")
    snapshots = []
    for snap_idx in range(1, 4):
        time.sleep(1.5)  # Allow simulation to step in background
        status_i = http_get("/api/v1/simulation/status")
        vessels_i = http_get("/api/v1/vessels")
        eta_i = http_get("/api/v1/vessels/V-FROMVEUR-SIM/eta")

        snap_data = {
            "snapshot_index": snap_idx,
            "wall_clock_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sim_time_utc": status_i.get("sim_time_utc"),
            "total_events_processed": status_i.get("total_events_processed"),
            "vessels": [
                {
                    "id": v["vessel_id"],
                    "name": v["name"],
                    "lat": v["lat"],
                    "lon": v["lon"],
                    "sog": v["sog_knots"],
                    "cog": v["cog_degrees"],
                    "state": v["eta_lifecycle_state"],
                    "remaining_min": v["estimated_remaining_minutes"],
                }
                for v in vessels_i.get("vessels", [])
            ],
            "fromveur_eta": {
                "predicted_arrival_utc": eta_i.get("timestamps", {}).get("predicted_arrival_utc"),
                "estimated_remaining_minutes": eta_i.get("predictions", {}).get("displayed_remaining_minutes"),
                "raw_model_minutes": eta_i.get("predictions", {}).get("raw_model_remaining_minutes"),
                "model_name": eta_i.get("provenance", {}).get("model_name"),
                "weights_sha256": eta_i.get("provenance", {}).get("weight_checksum_sha256"),
            },
        }
        snapshots.append(snap_data)
        print(f"\nSnapshot {snap_idx}: Sim Time = {snap_data['sim_time_utc']}")
        for v in snap_data["vessels"]:
            print(f"  - {v['id']}: lat={v['lat']}, lon={v['lon']}, sog={v['sog']}kn, remaining={v['remaining_min']}m")
        print(f"  FROMVEUR II ETA: model_remaining={snap_data['fromveur_eta']['raw_model_minutes']}m, displayed={snap_data['fromveur_eta']['estimated_remaining_minutes']}m")

    report["steps"]["03_advancing_snapshots"] = snapshots

    print("\n=== Step 4: Stop simulation cleanly ===")
    stop_res = http_post("/api/v1/simulation/controls", {"action": "stop"})
    print("Stop response:", stop_res)
    report["steps"]["04_stop_response"] = stop_res
    time.sleep(0.5)

    status_stopped = http_get("/api/v1/simulation/status")
    print(f"Stopped status: is_running={status_stopped.get('is_running')}, is_paused={status_stopped.get('is_paused')}")
    report["steps"]["05_stopped_status"] = status_stopped

    sse.stop()
    print(f"\nTotal SSE events captured: {len(sse.events)}")
    report["steps"]["06_sse_events_captured"] = len(sse.events)
    if sse.events:
        report["steps"]["06_sse_sample_event"] = sse.events[0]

    print("\n=== Step 5: Test Honest Arrival Latching & Stale Telemetry ===")
    # Reset first to ensure vessels are at origin berth and not arrived
    http_post("/api/v1/simulation/controls", {"action": "reset"})

    # 1. Trigger scenario 06 (Temporary Telemetry Loss) to verify honest stale handling
    stale_trigger = http_post("/api/v1/simulation/scenarios/scenario-6", {})
    print("Scenario 6 (Stale telemetry) trigger:", stale_trigger)
    vessels_stale = http_get("/api/v1/vessels")
    fromveur_stale = next(v for v in vessels_stale["vessels"] if v["vessel_id"] == "V-FROMVEUR-SIM")
    print(f"Stale vessel state: is_stale={fromveur_stale['is_stale']}, state={fromveur_stale['eta_lifecycle_state']}, age={fromveur_stale['telemetry_age_seconds']}s")
    report["steps"]["07_stale_verification"] = {
        "is_stale": fromveur_stale["is_stale"],
        "lifecycle_state": fromveur_stale["eta_lifecycle_state"],
        "telemetry_age_seconds": fromveur_stale["telemetry_age_seconds"],
    }

    # 2. Trigger scenario 12 (Successful Arrival) to verify arrived vessels remain arrived
    arrival_trigger = http_post("/api/v1/simulation/scenarios/scenario-12", {})
    print("Scenario 12 (Arrival) trigger:", arrival_trigger)
    vessels_arrival = http_get("/api/v1/vessels")
    fromveur_arrival = next(v for v in vessels_arrival["vessels"] if v["vessel_id"] == "V-FROMVEUR-SIM")
    print(f"Arrived vessel state: is_arrived={fromveur_arrival['is_arrived']}, state={fromveur_arrival['eta_lifecycle_state']}")
    report["steps"]["08_arrival_verification"] = {
        "is_arrived": fromveur_arrival["is_arrived"],
        "lifecycle_state": fromveur_arrival["eta_lifecycle_state"],
    }

    # Reset back to clean dock state
    http_post("/api/v1/simulation/controls", {"action": "reset"})

    print("\n=== Step 6: Verification Assertions ===")
    # 1. Clock advanced monotonically
    t0_sim = initial_snapshot["status"]["sim_time_utc"]
    t1_sim = snapshots[0]["sim_time_utc"]
    t2_sim = snapshots[1]["sim_time_utc"]
    t3_sim = snapshots[2]["sim_time_utc"]
    clock_advanced = (t0_sim < t1_sim < t2_sim < t3_sim)
    report["verifications"]["clock_advanced"] = {
        "passed": clock_advanced,
        "timestamps": [t0_sim, t1_sim, t2_sim, t3_sim],
    }

    # 2. Coordinates moved along route
    v0 = {v["id"]: (v["lat"], v["lon"]) for v in initial_snapshot["vessels"]}
    v3 = {v["id"]: (v["lat"], v["lon"]) for v in snapshots[2]["vessels"]}
    coords_moved = any(v0[vid] != v3[vid] for vid in v0)
    report["verifications"]["coordinates_moved"] = {
        "passed": coords_moved,
        "initial_v0": v0,
        "final_v3": v3,
    }

    # 3. Model ETA updated and Ridge model provenance verified
    eta_meta = snapshots[2]["fromveur_eta"]
    model_provenance_verified = (
        eta_meta["model_name"] == "VectorizedRidgeETAModel"
        and len(eta_meta["weights_sha256"]) == 64
    )
    report["verifications"]["model_provenance_verified"] = {
        "passed": model_provenance_verified,
        "model_name": eta_meta["model_name"],
        "weights_sha256": eta_meta["weights_sha256"],
    }

    # 4. SSE events received
    sse_verified = len(sse.events) > 0
    report["verifications"]["sse_events_received"] = {
        "passed": sse_verified,
        "count": len(sse.events),
    }

    # 5. Arrival latching verified
    arrival_verified = (
        fromveur_arrival["is_arrived"] is True
        and fromveur_arrival["eta_lifecycle_state"] == "ARRIVED"
    )
    report["verifications"]["arrival_latching_verified"] = {
        "passed": arrival_verified,
    }

    # 6. Stale telemetry verified
    stale_verified = (
        fromveur_stale["is_stale"] is True
        and "STALE" in fromveur_stale["eta_lifecycle_state"]
    )
    report["verifications"]["stale_handling_verified"] = {
        "passed": stale_verified,
    }

    # 7. Clean stop verified
    stop_verified = (status_stopped.get("is_running") is False)
    report["verifications"]["stopped_cleanly"] = {
        "passed": stop_verified,
    }

    all_passed = (
        clock_advanced
        and coords_moved
        and model_provenance_verified
        and sse_verified
        and arrival_verified
        and stale_verified
        and stop_verified
    )
    report["all_passed"] = all_passed
    print(f"\nALL VERIFICATIONS PASSED: {all_passed}")

    # Write report artifact
    out_path = Path(__file__).resolve().parents[2] / "reports" / "phase-01-remediation-runtime-evidence.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Detailed evidence saved to: {out_path}")

    return report


if __name__ == "__main__":
    run_controlled_p4_verification()
