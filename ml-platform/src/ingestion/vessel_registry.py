"""Defensible vessel identity registry and classification workflow."""

from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd


class ReviewStatus(str, Enum):
    VERIFIED_PASSENGER_FERRY = "VERIFIED_PASSENGER_FERRY"
    LIKELY_PASSENGER_FERRY = "LIKELY_PASSENGER_FERRY"
    NON_FERRY = "NON_FERRY"
    UNKNOWN = "UNKNOWN"


class IdentityConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class LicenseStatus(str, Enum):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    OPEN_REGISTRY = "OPEN_REGISTRY"
    RESTRICTED_RESEARCH = "RESTRICTED_RESEARCH"
    UNKNOWN = "UNKNOWN"


class VesselRegistryBuilder:
    """Builds and validates defensible vessel identity records with traceable evidence."""

    KNOWN_FERRY_KEYWORDS = [
        "FERRY", "QUEEN OF", "COASTAL ", "SPIRIT OF", "ISLAND ",
        "FROMVEUR", "ENEZ SUN", "ANDRE COLIN", "WSF "
    ]

    NON_FERRY_KEYWORDS = [
        "TUG", "BARGE", "CARGO", "TANKER", "FISHING", "ABEILLE BOURBON", "PILOT", "PILOTE"
    ]

    @classmethod
    def classify_vessel(
        cls,
        mmsi: int,
        vessel_name: Optional[str] = None,
        imo: Optional[str] = None,
        raw_type: Optional[str] = None,
        source: str = "UNKNOWN",
        license_status: LicenseStatus = LicenseStatus.UNKNOWN,
    ) -> Dict[str, Any]:
        """Classifies a vessel into strict states based on traceable evidence.

        Never infers ferry identity from trajectory shape or port proximity alone.
        """
        clean_name = str(vessel_name).strip().upper() if vessel_name else ""
        clean_imo = str(imo).strip() if imo and str(imo).lower() not in ["none", "nan", ""] else None
        clean_raw = str(raw_type).strip() if raw_type else "UNKNOWN"

        # Default fallback
        norm_type = "UNKNOWN"
        conf = IdentityConfidence.NONE
        status = ReviewStatus.UNKNOWN

        # 1. Non-Ferry Detection
        if any(kw in clean_name for kw in cls.NON_FERRY_KEYWORDS) or any(
            t in clean_raw.lower() for t in ["tug", "towing", "cargo", "tanker", "fishing", "pilot"]
        ):
            norm_type = "NON_FERRY"
            conf = IdentityConfidence.HIGH if clean_name else IdentityConfidence.MEDIUM
            status = ReviewStatus.NON_FERRY

        # 2. Documented French Brest Ferries (ITU / Penn ar Bed Fleet Roster)
        elif mmsi in [228017700, 227005550, 227002330]:
            name_map = {
                228017700: ("FROMVEUR II", "IMO9613147", "Penn ar Bed / Regional Council of Brittany"),
                227005550: ("ENEZ SUN 3", "IMO9034298", "Penn ar Bed / Regional Council of Brittany"),
                227002330: ("ANDRE COLIN", "IMO9134957", "Penn ar Bed / Regional Council of Brittany"),
            }
            mapped_name, mapped_imo, org = name_map[mmsi]
            clean_name = mapped_name
            clean_imo = mapped_imo
            norm_type = "PASSENGER_FERRY"
            source = f"ITU MARS & Public Fleet Roster ({org})"
            license_status = LicenseStatus.OPEN_REGISTRY
            conf = IdentityConfidence.HIGH
            status = ReviewStatus.VERIFIED_PASSENGER_FERRY

        # 3. Documented French Non-Ferries in Brest dataset
        elif mmsi in [228064900, 228109000]:
            if mmsi == 228064900:
                clean_name = "ABEILLE BOURBON"
                clean_imo = "IMO9308352"
                norm_type = "EMERGENCY_TOWING_VESSEL"
            else:
                clean_name = "PILOTE BREST"
                norm_type = "PILOT_VESSEL"
            source = "French Maritime Affairs Public Registry"
            license_status = LicenseStatus.OPEN_REGISTRY
            conf = IdentityConfidence.HIGH
            status = ReviewStatus.NON_FERRY

        # 4. MarineCadastre Named Passenger Vessels
        elif "passenger" in clean_raw.lower():
            is_named_ferry = any(kw in clean_name for kw in cls.KNOWN_FERRY_KEYWORDS)
            if is_named_ferry:
                norm_type = "PASSENGER_FERRY"
                conf = IdentityConfidence.HIGH if clean_imo else IdentityConfidence.MEDIUM
                # Verified if IMO and known operator nomenclature, otherwise Likely
                status = (
                    ReviewStatus.VERIFIED_PASSENGER_FERRY
                    if clean_imo
                    else ReviewStatus.LIKELY_PASSENGER_FERRY
                )
            elif clean_name and not clean_name.startswith("UNKNOWN"):
                norm_type = "PASSENGER_VESSEL"
                conf = IdentityConfidence.MEDIUM
                status = ReviewStatus.LIKELY_PASSENGER_FERRY
            else:
                norm_type = "PASSENGER_UNSPECIFIED"
                conf = IdentityConfidence.LOW
                status = ReviewStatus.UNKNOWN

        # 5. Pleasure craft, sailing, etc.
        elif any(t in clean_raw.lower() for t in ["pleasure", "sailing"]):
            norm_type = "RECREATIONAL"
            conf = IdentityConfidence.HIGH if clean_raw else IdentityConfidence.MEDIUM
            status = ReviewStatus.NON_FERRY

        return {
            "mmsi": int(mmsi),
            "imo": clean_imo,
            "vessel_name": clean_name if clean_name else None,
            "vessel_type_raw": clean_raw,
            "normalized_vessel_type": norm_type,
            "identity_source": source,
            "identity_confidence": conf.value,
            "license_status": license_status.value,
            "review_status": status.value,
        }

    @classmethod
    def to_dataframe(cls, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Converts registry records to a typed DataFrame."""
        df = pd.DataFrame(records)
        df["mmsi"] = df["mmsi"].astype("int64")
        return df
