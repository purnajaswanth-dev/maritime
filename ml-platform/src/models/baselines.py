"""Deterministic, leakage-safe ETA baselines for passenger ferry voyages.

Includes:
1. PhysicalETABaseline: Speed-distance kinematic projection with nautical limitations.
2. HistoricalRouteDurationBaseline: Causally masked historical route median duration.
3. DescriptiveCorridorBaseline: Simple global corridor median for benchmark reference.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class PhysicalETABaseline:
    """Estimates remaining travel time from remaining navigable distance and current speed.

    Safety rules:
    - Rejects missing, zero, negative, or implausible (> 50 knots) speeds.
    - Flags straight-line distance approximations explicitly as nautical underestimates.
    - Uses only information available at the prediction timestamp.
    """

    MIN_PLAUSIBLE_SPEED_KNOTS = 0.5
    MAX_PLAUSIBLE_SPEED_KNOTS = 50.0  # Commercial passenger ferries rarely exceed 45 knots

    @classmethod
    def predict(
        cls,
        remaining_distance_nm: Optional[float],
        current_speed_knots: Optional[float],
        is_straight_line_distance: bool = False,
    ) -> Dict[str, Any]:
        """Calculates remaining travel time in minutes.

        Returns:
            Dict containing predicted_remaining_minutes, status, baseline_name, and limitations.
        """
        limitations: List[str] = []

        if remaining_distance_nm is None or np.isnan(remaining_distance_nm) or remaining_distance_nm < 0:
            return {
                "baseline_name": "PHYSICAL_SPEED_DISTANCE",
                "predicted_remaining_minutes": None,
                "status": "UNAVAILABLE_DISTANCE",
                "limitations": ["Remaining navigable distance is missing or negative."],
            }

        if is_straight_line_distance:
            limitations.append(
                "Straight-line Euclidean/Haversine distance underestimates actual navigable fairway distance."
            )

        if (
            current_speed_knots is None
            or np.isnan(current_speed_knots)
            or current_speed_knots < cls.MIN_PLAUSIBLE_SPEED_KNOTS
        ):
            limitations.append(
                f"Vessel speed ({current_speed_knots}) is zero, missing, or below navigation threshold (< {cls.MIN_PLAUSIBLE_SPEED_KNOTS} kn)."
            )
            return {
                "baseline_name": "PHYSICAL_SPEED_DISTANCE",
                "predicted_remaining_minutes": None,
                "status": "UNAVAILABLE_SPEED",
                "limitations": limitations,
            }

        if current_speed_knots > cls.MAX_PLAUSIBLE_SPEED_KNOTS:
            limitations.append(
                f"Vessel speed ({current_speed_knots} kn) exceeds plausible passenger ferry threshold ({cls.MAX_PLAUSIBLE_SPEED_KNOTS} kn)."
            )
            return {
                "baseline_name": "PHYSICAL_SPEED_DISTANCE",
                "predicted_remaining_minutes": None,
                "status": "IMPLAUSIBLE_SPEED",
                "limitations": limitations,
            }

        # Calculate kinematic remaining travel time: (distance / speed) * 60 minutes
        remaining_hours = remaining_distance_nm / current_speed_knots
        remaining_minutes = round(remaining_hours * 60.0, 2)

        return {
            "baseline_name": "PHYSICAL_SPEED_DISTANCE",
            "predicted_remaining_minutes": remaining_minutes,
            "status": "AVAILABLE",
            "limitations": limitations,
        }


class HistoricalRouteDurationBaseline:
    """Estimates remaining travel time using historical verified voyages on the same route.

    Safety rules:
    - Causality enforcement: strictly filters out voyages occurring on or after prediction_timestamp_utc.
    - Excludes the current voyage from historical statistics.
    - Requires an explicitly configured minimum number of historical observations.
    - Computes remaining duration as max(0.0, median_historical_duration - elapsed_minutes).
    """

    def __init__(self, min_history_count: int = 3):
        self.min_history_count = min_history_count

    def predict(
        self,
        route_id: str,
        elapsed_minutes: float,
        prediction_timestamp_utc: str,
        history_df: pd.DataFrame,
        current_voyage_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Predicts remaining travel time based on past verified voyages on route_id.

        Required columns in history_df:
            ['route_id', 'departure_timestamp_utc', 'actual_duration_minutes', 'voyage_id']
        """
        if history_df is None or history_df.empty:
            return {
                "baseline_name": "HISTORICAL_ROUTE_MEDIAN",
                "predicted_remaining_minutes": None,
                "status": "NO_HISTORICAL_DATA",
                "sample_count": 0,
                "median_duration_minutes": None,
            }

        # 1. Filter by route_id
        route_mask = history_df["route_id"] == route_id

        # 2. Strict causal completion filter: only voyages strictly completed prior to prediction_timestamp_utc
        pred_ts = pd.to_datetime(prediction_timestamp_utc, utc=True)
        dep_ts = pd.to_datetime(history_df["departure_timestamp_utc"], utc=True)

        # A voyage is completed if its arrival timestamp <= pred_ts.
        # If explicit arrival_timestamp_utc is missing, compute from departure + actual_duration_minutes.
        if "arrival_timestamp_utc" in history_df.columns and history_df["arrival_timestamp_utc"].notna().any():
            arr_ts = pd.to_datetime(history_df["arrival_timestamp_utc"], utc=True)
        else:
            arr_ts = dep_ts + pd.to_timedelta(history_df["actual_duration_minutes"], unit="m")

        # Must have completed before or at prediction time
        temporal_mask = arr_ts <= pred_ts

        # 3. Exclude current voyage
        if current_voyage_id and "voyage_id" in history_df.columns:
            voyage_mask = history_df["voyage_id"] != current_voyage_id
        else:
            voyage_mask = pd.Series(True, index=history_df.index)

        valid_history = history_df[route_mask & temporal_mask & voyage_mask]
        sample_count = len(valid_history)

        if sample_count < self.min_history_count:
            return {
                "baseline_name": "HISTORICAL_ROUTE_MEDIAN",
                "predicted_remaining_minutes": None,
                "status": "INSUFFICIENT_HISTORY",
                "sample_count": sample_count,
                "median_duration_minutes": None,
                "reason": f"Only {sample_count} prior voyages available (minimum required: {self.min_history_count}).",
            }

        median_duration = float(valid_history["actual_duration_minutes"].median())
        remaining_minutes = max(0.0, round(median_duration - elapsed_minutes, 2))

        return {
            "baseline_name": "HISTORICAL_ROUTE_MEDIAN",
            "predicted_remaining_minutes": remaining_minutes,
            "status": "AVAILABLE",
            "sample_count": sample_count,
            "median_duration_minutes": round(median_duration, 2),
        }


class DescriptiveCorridorBaseline:
    """Descriptive reference computing global corridor median duration.

    This baseline provides a static descriptive benchmark for dataset variance analysis.
    It is NOT an operational model.
    """

    @classmethod
    def predict(
        cls,
        corridor_id: str,
        elapsed_minutes: float,
        history_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Computes remaining duration against the overall corridor median duration."""
        if history_df is None or history_df.empty or "actual_duration_minutes" not in history_df.columns:
            return {
                "baseline_name": "DESCRIPTIVE_CORRIDOR_MEDIAN",
                "predicted_remaining_minutes": None,
                "status": "NO_DATA",
            }

        corridor_mask = history_df["corridor_id"] == corridor_id if "corridor_id" in history_df.columns else pd.Series(True, index=history_df.index)
        samples = history_df[corridor_mask]["actual_duration_minutes"].dropna()

        if len(samples) == 0:
            return {
                "baseline_name": "DESCRIPTIVE_CORRIDOR_MEDIAN",
                "predicted_remaining_minutes": None,
                "status": "NO_CORRIDOR_DATA",
            }

        global_median = float(samples.median())
        remaining = max(0.0, round(global_median - elapsed_minutes, 2))

        return {
            "baseline_name": "DESCRIPTIVE_CORRIDOR_MEDIAN",
            "predicted_remaining_minutes": remaining,
            "status": "AVAILABLE",
            "corridor_sample_count": len(samples),
            "corridor_median_minutes": round(global_median, 2),
            "note": "Descriptive benchmark only; not an operational predictive model.",
        }
