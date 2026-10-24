"""Driver script executing investigation of US AIS tracks and vessel matches."""

from src.ingestion.us_ais_investigator import USAISInvestigator
from src.profiling.gtfs_profiler import GTFSProfiler


def run():
    print("=" * 65)
    print("TASK 3 INVESTIGATION: US AIS TRACK SOURCE & VESSEL DISTRIBUTION")
    print("=" * 65)

    inv = USAISInvestigator()
    print("\n1. Running statistical sampling (20,000 features)...")
    dist = inv.compute_vessel_type_distribution(sample_size=20000)
    print(f"Sample Size: {dist['sample_size']} features")
    for k, v in sorted(dist["distribution"].items(), key=lambda x: -x[1]["sample_count"])[:10]:
        pct = v["proportion"] * 100
        moe = v["margin_of_error_95pct"] * 100
        print(f"  - {k:35}: {v['sample_count']:5} ({pct:5.2f}% +/- {moe:4.2f}%) [CI: {v['ci_lower']*100:.2f}% - {v['ci_upper']*100:.2f}%]")

    print("\n2. Querying distinct Passenger Vessels in dataset...")
    df_pass = inv.query_passenger_vessels(limit=10000)
    print(f"Total passenger track rows queried in slice: {len(df_pass)}")
    unique_vessels = df_pass.drop_duplicates(subset=["mmsi"])
    print(f"Distinct Passenger MMSIs found: {len(unique_vessels)}")

    print("\n3. Testing for known ferry names (e.g., Ferries, Queen, Salish, etc.):")
    ferry_keywords = ["FERRY", "QUEEN", "SALISH", "COASTAL", "SPIRIT", "ISLAND", "WENATCHEE", "TACOMA", "CHELAN"]
    matched_vessels = []
    for idx, row in unique_vessels.iterrows():
        vname = str(row["vessel_name"]).upper()
        if any(kw in vname for kw in ferry_keywords):
            matched_vessels.append(row)

    print(f"Found {len(matched_vessels)} candidate ferry vessels matching common ferry nomenclature in sample:")
    for v in matched_vessels[:15]:
        print(f"  MMSI: {v['mmsi']} | Name: {v['vessel_name']} | IMO: {v['imo']} | Type: {v['vessel_type_name']} | Len: {v['vessel_length']}m")

    # 4. Check BC Ferries overlap in Southern Salish Sea window
    print("\n4. Checking Southern Salish Sea / BC border window (Bbox: [-124.5, 48.0, -122.5, 49.5])...")
    df_salish = inv.query_spatial_window(
        min_lon=-124.5, min_lat=48.0, max_lon=-122.5, max_lat=49.5, limit=500
    )
    print(f"Tracks in Salish Sea window: {len(df_salish)}")
    salish_vessels = df_salish["vessel_name"].value_counts().head(10)
    for name, cnt in salish_vessels.items():
        print(f"  {name}: {cnt} tracks")


if __name__ == "__main__":
    run()
