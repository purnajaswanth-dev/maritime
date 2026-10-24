"""Tests verifying VirtualFleetRunner lifecycle management and thread safety.

Covers:
- start -> advance -> pause -> resume -> stop sequence
- resume on never-started simulation starting the loop
- repeated control requests (idempotency and safety)
- duplicate thread prevention
- reset cleanly restoring initial state
"""

from datetime import datetime, timezone
import time
import pytest

from src.simulation.virtual_fleet_runner import VirtualFleetRunner, SimulationStatus


def test_start_advance_pause_resume_stop_lifecycle():
    """Verify standard lifecycle transitions: start -> advance -> pause -> resume -> stop."""
    runner = VirtualFleetRunner()
    assert not runner.is_running
    assert not runner.is_paused

    # 1. Start simulation
    runner.start(speed_multiplier=10.0, step_interval_s=5.0)
    assert runner.is_running
    assert not runner.is_paused
    initial_thread = runner._thread
    assert initial_thread is not None and initial_thread.is_alive()

    # Let simulation loop advance slightly
    time.sleep(0.15)
    status = runner.get_status()
    assert status.is_running
    assert status.total_events_generated > 0

    # 2. Pause simulation
    runner.pause()
    assert runner.is_paused
    assert runner.is_running
    time.sleep(0.05)
    gen_at_pause = runner.get_status().total_events_generated

    # Clock/generation should pause
    time.sleep(0.1)
    status_paused = runner.get_status()
    assert status_paused.is_paused
    assert status_paused.total_events_generated == gen_at_pause

    # 3. Resume simulation
    runner.resume()
    assert not runner.is_paused
    assert runner.is_running

    # Should resume generating events
    time.sleep(0.15)
    status_resumed = runner.get_status()
    assert status_resumed.total_events_generated > gen_at_pause

    # 4. Stop simulation
    runner.stop()
    assert not runner.is_running
    assert not runner.is_paused
    assert runner._thread is None
    assert not initial_thread.is_alive()


def test_resume_on_never_started_simulation():
    """Verify that calling resume on a never-started simulation starts the execution loop."""
    runner = VirtualFleetRunner()
    assert not runner.is_running
    assert not runner.is_paused

    runner.resume()
    assert runner.is_running
    assert not runner.is_paused
    assert runner._thread is not None
    assert runner._thread.is_alive()

    time.sleep(0.1)
    runner.stop()
    assert not runner.is_running


def test_repeated_control_calls_safety():
    """Verify that repeated / redundant control calls do not crash or corrupt runner state."""
    runner = VirtualFleetRunner()

    # Repeated stop when already stopped
    runner.stop()
    runner.stop()
    assert not runner.is_running

    # Repeated pause when stopped
    runner.pause()
    runner.pause()
    assert runner.is_paused

    # Start runner
    runner.start(speed_multiplier=5.0)
    first_thread = runner._thread
    assert runner.is_running
    assert not runner.is_paused  # start clears pause

    # Repeated start when already running (should update multiplier and NOT spawn duplicate thread)
    runner.start(speed_multiplier=12.0)
    assert runner._thread is first_thread
    assert runner.speed_multiplier == 12.0
    assert runner.is_running

    # Repeated pause when running
    runner.pause()
    runner.pause()
    assert runner.is_paused
    assert runner.is_running

    # Repeated resume
    runner.resume()
    runner.resume()
    assert not runner.is_paused
    assert runner.is_running

    # Clean shutdown
    runner.stop()
    assert not runner.is_running


def test_reset_lifecycle_and_state_cleanup():
    """Verify that reset stops active execution and cleanly restores baseline simulation state."""
    runner = VirtualFleetRunner()
    runner.start(speed_multiplier=20.0, step_interval_s=10.0)
    time.sleep(0.15)

    assert runner.is_running
    assert runner.total_events_generated > 0

    # Trigger reset
    runner.reset()

    # Runner must be stopped, not paused, and have baseline time
    assert not runner.is_running
    assert not runner.is_paused
    assert runner._thread is None
    assert runner.current_sim_time == datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
    assert runner.total_events_generated == 4  # 4 initial pre-step events
    assert runner.total_events_processed == 4
    assert len(runner.generator.get_vessel_ids()) == 4
