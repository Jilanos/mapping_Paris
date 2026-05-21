import argparse

from app.db.session import SessionLocal, init_db
from app.services.segment_dataset_parser import SegmentDatasetParser
from app.services.segment_dataset_store import SegmentDatasetStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the Paris segment GeoJSON dataset.")
    parser.add_argument("--source", required=True, help="Path to paris_segments.geojson")
    parser.add_argument("--notes", default=None, help="Optional dataset notes")
    args = parser.parse_args()

    init_db()
    parsed = SegmentDatasetParser().parse_file(args.source)
    with SessionLocal() as db:
        version = SegmentDatasetStore(db).ingest(parsed, notes=args.notes)
        print(f"dataset_hash={version.dataset_hash}")
        print(f"segment_count={version.segment_count}")
        print(f"logical_segment_count={version.logical_segment_count}")
        print(f"active_version_id={version.id}")


if __name__ == "__main__":
    main()
