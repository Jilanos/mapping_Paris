import json

from sqlalchemy.orm import Session

from app.db.models import B2StreetSegment, SegmentDatasetVersion
from app.services.segment_dataset_parser import ParsedSegmentDataset


class SegmentDatasetStore:
    def __init__(self, db: Session) -> None:
        self._db = db

    def ingest(self, dataset: ParsedSegmentDataset, notes: str | None = None) -> SegmentDatasetVersion:
        existing = (
            self._db.query(SegmentDatasetVersion)
            .filter(SegmentDatasetVersion.dataset_hash == dataset.dataset_hash)
            .one_or_none()
        )
        if existing is not None:
            self._activate(existing)
            return existing

        version = SegmentDatasetVersion(
            dataset_hash=dataset.dataset_hash,
            source_path=dataset.source_path,
            source_file_name=dataset.source_file_name,
            source_file_size_bytes=dataset.source_file_size_bytes,
            segment_count=dataset.segment_count,
            logical_segment_count=dataset.logical_segment_count,
            is_active=True,
            notes=notes,
        )
        self._db.query(SegmentDatasetVersion).update({SegmentDatasetVersion.is_active: False})
        self._db.add(version)
        self._db.commit()
        self._db.refresh(version)

        self._db.add_all(
            [
                B2StreetSegment(
                    dataset_version_id=version.id,
                    segment_id=segment.segment_id,
                    logical_segment_id=segment.logical_segment_id,
                    street_name=segment.street_name,
                    arrondissement=segment.arrondissement,
                    length_meters=segment.length_meters,
                    accessibility=segment.accessibility,
                    geometry_json=json.dumps(segment.geometry, separators=(",", ":")),
                    min_lat=segment.min_lat,
                    min_lon=segment.min_lon,
                    max_lat=segment.max_lat,
                    max_lon=segment.max_lon,
                )
                for segment in dataset.segments
            ]
        )
        self._db.commit()
        self._db.refresh(version)
        return version

    def active_version(self) -> SegmentDatasetVersion | None:
        return (
            self._db.query(SegmentDatasetVersion)
            .filter(SegmentDatasetVersion.is_active.is_(True))
            .order_by(SegmentDatasetVersion.created_at.desc(), SegmentDatasetVersion.id.desc())
            .first()
        )

    def recent_versions(self, limit: int = 20) -> list[SegmentDatasetVersion]:
        return (
            self._db.query(SegmentDatasetVersion)
            .order_by(SegmentDatasetVersion.created_at.desc(), SegmentDatasetVersion.id.desc())
            .limit(limit)
            .all()
        )

    def search_segments(
        self,
        arrondissement: str | None = None,
        street_name: str | None = None,
        limit: int = 50,
    ) -> list[B2StreetSegment]:
        active = self.active_version()
        if active is None:
            return []
        query = self._db.query(B2StreetSegment).filter(
            B2StreetSegment.dataset_version_id == active.id
        )
        if arrondissement:
            query = query.filter(B2StreetSegment.arrondissement == arrondissement)
        if street_name:
            query = query.filter(B2StreetSegment.street_name.ilike(f"%{street_name}%"))
        return query.order_by(B2StreetSegment.street_name.asc(), B2StreetSegment.id.asc()).limit(limit).all()

    def _activate(self, version: SegmentDatasetVersion) -> None:
        self._db.query(SegmentDatasetVersion).update({SegmentDatasetVersion.is_active: False})
        version.is_active = True
        self._db.add(version)
        self._db.commit()
        self._db.refresh(version)
