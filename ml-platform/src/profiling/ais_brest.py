"""Safe, streaming inspector for datAcron Brest AIS zip archive."""

import csv
import io
import os
import zipfile
from typing import Any, Dict, List, Optional


class AISBrestProfiler:
    """Streams metadata and sample records from ais_brest_synopses_v0.8.zip without disk extraction."""

    def __init__(self, zip_path: str):
        self.zip_path = os.path.normpath(zip_path).replace("\\", "/")

    def inspect_readme(self) -> str:
        """Reads documentation text file directly from archive."""
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            readme_data = zf.read("ais_brest_synopses_v0.8_ReadMe.txt")
            return readme_data.decode("utf-8", errors="replace")

    def sample_csv_member(
        self, member_name: str, max_rows: int = 10
    ) -> Dict[str, Any]:
        """Streams header and bounded row sample from a large CSV member without full decompression."""
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            with zf.open(member_name, "r") as raw_file:
                # Wrap with TextIOWrapper for streaming line by line
                text_stream = io.TextIOWrapper(raw_file, encoding="utf-8", errors="replace")
                reader = csv.reader(text_stream)
                try:
                    header = next(reader)
                except StopIteration:
                    return {"header": [], "sample_rows": [], "row_count_sampled": 0}

                sample_rows = []
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    sample_rows.append(row)

                return {
                    "member_name": member_name,
                    "header": header,
                    "num_columns": len(header),
                    "sample_rows": sample_rows,
                    "row_count_sampled": len(sample_rows),
                }

    def profile_fields(self, member_name: str) -> Dict[str, Any]:
        """Profiles columns, data types, and presence of vessel type / ferry identifiers."""
        sample_info = self.sample_csv_member(member_name, max_rows=50)
        header = sample_info["header"]
        sample_rows = sample_info["sample_rows"]

        # Check for ferry/vessel type indicators
        vessel_type_indicators = [
            c for c in header if any(kw in c.lower() for kw in ["type", "vessel", "ship", "category", "ferry"])
        ]

        # Infer simple types from sample
        inferred_types = {}
        for idx, col in enumerate(header):
            values = [row[idx] for row in sample_rows if idx < len(row)]
            if not values:
                inferred_types[col] = "Empty"
                continue
            is_float = True
            is_int = True
            for v in values:
                try:
                    int(v)
                except ValueError:
                    is_int = False
                try:
                    float(v)
                except ValueError:
                    is_float = False
            if is_int:
                inferred_types[col] = "Integer"
            elif is_float:
                inferred_types[col] = "Float"
            else:
                inferred_types[col] = "String"

        return {
            "member_name": member_name,
            "header": header,
            "inferred_types": inferred_types,
            "vessel_type_indicators": vessel_type_indicators,
            "has_vessel_type_column": len(vessel_type_indicators) > 0,
        }
