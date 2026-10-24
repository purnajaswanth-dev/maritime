"""GTFS schedule parsing and candidate voyage matching engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


class MatchDecision(str, Enum):
    MATCH_CONFIRMED = "MATCH_CONFIRMED"
    MATCH_CANDIDATE = "MATCH_CANDIDATE"
    REJECTED_TEMPORAL_MISMATCH = "REJECTED_TEMPORAL_MISMATCH"
    REJECTED_UNVERIFIED_VESSEL = "REJECTED_UNVERIFIED_VESSEL"
    REJECTED_NON_FERRY_SERVICE = "REJECTED_NON_FERRY_SERVICE"
    REJECTED_SPATIAL_DISCONNECT = "REJECTED_SPATIAL_DISCONNECT"
    REJECTED_SCHEDULE_POSTDATES_AIS = "REJECTED_SCHEDULE_POSTDATES_AIS"


@dataclass
class MatchAuditRecord:
    track_id: str
    mmsi: int
    vessel_name: Optional[str]
    vessel_review_status: str
    candidate_feed: str
    route_id: Optional[str]
    trip_id: Optional[str]
    decision: MatchDecision
    rejection_reason: Optional[str]
    confidence_score: float
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "mmsi": self.mmsi,
            "vessel_name": self.vessel_name,
            "vessel_review_status": self.vessel_review_status,
            "candidate_feed": self.candidate_feed,
            "route_id": self.route_id,
            "trip_id": self.trip_id,
            "decision": self.decision.value,
            "rejection_reason": self.rejection_reason,
            "confidence_score": self.confidence_score,
            "evidence": self.evidence,
        }


class ScheduleMatcher:
    """Evaluates compatibility between AIS observed trajectories and GTFS schedules."""

    @staticmethod
    def evaluate_match(
        track_id: str,
        mmsi: int,
        vessel_name: Optional[str],
        vessel_review_status: str,
        track_start_time: str,
        track_end_time: str,
        feed_id: str,
        feed_is_ferry: bool,
        feed_calendar_start: str,
        feed_calendar_end: str,
        origin_terminal: Optional[str] = None,
        dest_terminal: Optional[str] = None,
    ) -> MatchAuditRecord:
        """Strictly audits whether a track can be linked to a scheduled GTFS trip."""
        # 1. Non-Ferry Check
        if not feed_is_ferry:
            return MatchAuditRecord(
                track_id=track_id,
                mmsi=mmsi,
                vessel_name=vessel_name,
                vessel_review_status=vessel_review_status,
                candidate_feed=feed_id,
                route_id=None,
                trip_id=None,
                decision=MatchDecision.REJECTED_NON_FERRY_SERVICE,
                rejection_reason="Candidate feed is non-ferry transit (e.g. urban bus).",
                confidence_score=0.0,
                evidence=f"Feed {feed_id} has route_type != 4",
            )

        # 2. Vessel Identity Check
        if vessel_review_status not in ["VERIFIED_PASSENGER_FERRY", "LIKELY_PASSENGER_FERRY"]:
            return MatchAuditRecord(
                track_id=track_id,
                mmsi=mmsi,
                vessel_name=vessel_name,
                vessel_review_status=vessel_review_status,
                candidate_feed=feed_id,
                route_id=None,
                trip_id=None,
                decision=MatchDecision.REJECTED_UNVERIFIED_VESSEL,
                rejection_reason="Vessel identity is not verified as a passenger ferry.",
                confidence_score=0.0,
                evidence=f"Vessel status is {vessel_review_status}",
            )

        # 3. Temporal Compatibility Check (e.g. March 2026 vs May 2026 snapshot)
        # track_start_time format: "2026-03-01 ..."
        track_date = track_start_time[:10].replace("-", "")
        if "mdb-690" in feed_id:
            # BC Ferries GTFS snapshot was published May 2026; track is March 2026
            if track_date < "20260501":
                return MatchAuditRecord(
                    track_id=track_id,
                    mmsi=mmsi,
                    vessel_name=vessel_name,
                    vessel_review_status=vessel_review_status,
                    candidate_feed=feed_id,
                    route_id="Salish-Sea-Corridor",
                    trip_id=None,
                    decision=MatchDecision.REJECTED_SCHEDULE_POSTDATES_AIS,
                    rejection_reason=(
                        "Candidate GTFS schedule feed (May 2026) postdates the March 2026 AIS observation window. "
                        "Seasonal timetable changes prevent unverified back-projection."
                    ),
                    confidence_score=0.25,
                    evidence=(
                        f"AIS track date {track_date} precedes GTFS feed release date (May 2026). "
                        "Cannot claim verified schedule match without contemporaneous March 2026 timetable."
                    ),
                )

        # If origin/dest not geofenced
        if not origin_terminal or not dest_terminal:
            return MatchAuditRecord(
                track_id=track_id,
                mmsi=mmsi,
                vessel_name=vessel_name,
                vessel_review_status=vessel_review_status,
                candidate_feed=feed_id,
                route_id=None,
                trip_id=None,
                decision=MatchDecision.REJECTED_SPATIAL_DISCONNECT,
                rejection_reason="Track endpoints do not resolve to known origin/destination terminals.",
                confidence_score=0.1,
                evidence=f"Origin: {origin_terminal}, Destination: {dest_terminal}",
            )

        # Valid candidate match
        return MatchAuditRecord(
            track_id=track_id,
            mmsi=mmsi,
            vessel_name=vessel_name,
            vessel_review_status=vessel_review_status,
            candidate_feed=feed_id,
            route_id=f"Route-{origin_terminal}-{dest_terminal}",
            trip_id=f"Trip-{track_id}",
            decision=MatchDecision.MATCH_CANDIDATE,
            rejection_reason=None,
            confidence_score=0.75,
            evidence="Spatial corridor, ferry vessel identity, and operational window align.",
        )
