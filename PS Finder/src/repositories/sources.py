from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.source import AuthorityLevel, SourceRegistryEntry
from src.repositories.database import SourceTable


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, enabled_only: bool = True) -> List[SourceRegistryEntry]:
        query = self.db.query(SourceTable)
        if enabled_only:
            query = query.filter(SourceTable.enabled == True)
        rows = query.all()
        return [
            SourceRegistryEntry(
                source_id=r.source_id,
                name=r.name,
                organization=r.organization,
                organization_type=r.organization_type,
                country=r.country,
                authority_level=AuthorityLevel(r.authority_level),
                base_url=r.base_url,
                enabled=r.enabled,
                adapter=r.adapter,
                discovery_frequency=r.discovery_frequency
            )
            for r in rows
        ]

    def upsert(self, entry: SourceRegistryEntry):
        existing = self.db.query(SourceTable).filter(SourceTable.source_id == entry.source_id).first()
        if not existing:
            row = SourceTable(
                source_id=entry.source_id,
                name=entry.name,
                organization=entry.organization,
                organization_type=entry.organization_type,
                country=entry.country,
                authority_level=entry.authority_level.value,
                base_url=entry.base_url,
                enabled=entry.enabled,
                adapter=entry.adapter,
                discovery_frequency=entry.discovery_frequency
            )
            self.db.add(row)
        else:
            existing.name = entry.name
            existing.organization = entry.organization
            existing.organization_type = entry.organization_type
            existing.country = entry.country
            existing.authority_level = entry.authority_level.value
            existing.base_url = entry.base_url
            existing.enabled = entry.enabled
            existing.adapter = entry.adapter
            existing.discovery_frequency = entry.discovery_frequency

        self.db.commit()

    def update_last_run(self, source_id: str):
        existing = self.db.query(SourceTable).filter(SourceTable.source_id == source_id).first()
        if existing:
            existing.last_run_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.commit()

