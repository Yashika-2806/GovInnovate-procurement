import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.evidence import Evidence
from src.models.organization import Organization, OrganizationType
from src.models.source import SourceInfo, VerificationStatus
from src.models.opportunity import (
    Geography, FundingInfo, Opportunity, OpportunityStatus, OpportunityType, PrizeInfo
)
from src.models.version import FieldDiff, OpportunityVersion
from src.repositories.database import OpportunityTable, VersionTable

logger = logging.getLogger(__name__)


class OpportunityRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_model(self, table: OpportunityTable) -> Opportunity:
        domains = json.loads(table.domains) if table.domains else []
        eligibility = json.loads(table.eligibility) if table.eligibility else []
        requirements = json.loads(table.requirements) if table.requirements else []
        constraints = json.loads(table.constraints) if table.constraints else []
        
        evidence_dicts = json.loads(table.source_evidence) if table.source_evidence else []
        evidence_list = [Evidence(**e) for e in evidence_dicts]

        prize = None
        if table.prize_amount is not None or table.prize_raw:
            prize = PrizeInfo(
                amount=table.prize_amount,
                currency=table.prize_currency or "INR",
                raw_text=table.prize_raw
            )

        funding = None
        if table.funding_amount is not None or table.funding_raw:
            funding = FundingInfo(
                amount=table.funding_amount,
                currency=table.funding_currency or "INR",
                raw_text=table.funding_raw
            )

        return Opportunity(
            id=table.id,
            title=table.title,
            problem_statement=table.problem_statement,
            organization=Organization(
                name=table.organization_name,
                type=OrganizationType(table.organization_type) if table.organization_type in [e.value for e in OrganizationType] else OrganizationType.GOVERNMENT,
                level=table.organization_level
            ),
            opportunity_type=OpportunityType(table.opportunity_type) if table.opportunity_type in [e.value for e in OpportunityType] else OpportunityType.INNOVATION_CHALLENGE,
            source_opportunity_type=table.source_opportunity_type,
            domains=domains,
            geography=Geography(
                country=table.country,
                region=table.region,
                city=table.city
            ),
            status=OpportunityStatus(table.status) if table.status in [e.value for e in OpportunityStatus] else OpportunityStatus.ACTIVE,
            published_date=table.published_date,
            deadline=table.deadline,
            prize=prize,
            funding=funding,
            support=table.support_description,
            eligibility=eligibility,
            requirements=requirements,
            constraints=constraints,
            expected_outcome=table.expected_outcome,
            verification_status=VerificationStatus(table.verification_status) if table.verification_status in [e.value for e in VerificationStatus] else VerificationStatus.VERIFIED_OFFICIAL,
            source=SourceInfo(
                url=table.source_url,
                source_domain=table.source_domain,
                source_title=table.source_title,
                issuing_organization=table.organization_name,
                published_date=table.published_date,
                last_verified_at=table.last_verified_at
            ),
            source_evidence=evidence_list,
            version=table.version,
            unverified_duplicate_of=table.unverified_duplicate_of,
            first_seen_at=table.first_seen_at,
            last_verified_at=table.last_verified_at,
            last_changed_at=table.last_changed_at
        )

    def _to_table(self, opp: Opportunity) -> OpportunityTable:
        evidence_dicts = [e.model_dump(mode="json") for e in opp.source_evidence]
        return OpportunityTable(
            id=opp.id,
            title=opp.title,
            problem_statement=opp.problem_statement,
            organization_name=opp.organization.name,
            organization_type=opp.organization.type.value,
            organization_level=opp.organization.level,
            opportunity_type=opp.opportunity_type.value,
            source_opportunity_type=opp.source_opportunity_type,
            domains=json.dumps(opp.domains),
            country=opp.geography.country,
            region=opp.geography.region,
            city=opp.geography.city,
            status=opp.status.value,
            published_date=opp.published_date,
            deadline=opp.deadline,
            prize_amount=opp.prize.amount if opp.prize else None,
            prize_currency=opp.prize.currency if opp.prize else "INR",
            prize_raw=opp.prize.raw_text if opp.prize else None,
            funding_amount=opp.funding.amount if opp.funding else None,
            funding_currency=opp.funding.currency if opp.funding else "INR",
            funding_raw=opp.funding.raw_text if opp.funding else None,
            support_description=opp.support,
            eligibility=json.dumps(opp.eligibility),
            requirements=json.dumps(opp.requirements),
            constraints=json.dumps(opp.constraints),
            expected_outcome=opp.expected_outcome,
            verification_status=opp.verification_status.value,
            source_url=opp.source.url,
            source_domain=opp.source.source_domain,
            source_title=opp.source.source_title,
            source_evidence=json.dumps(evidence_dicts),
            version=opp.version,
            unverified_duplicate_of=opp.unverified_duplicate_of,
            first_seen_at=opp.first_seen_at,
            last_verified_at=opp.last_verified_at,
            last_changed_at=opp.last_changed_at
        )

    def get_by_id(self, opp_id: str) -> Optional[Opportunity]:
        table = self.db.query(OpportunityTable).filter(OpportunityTable.id == opp_id).first()
        return self._to_model(table) if table else None

    def get_by_source_url(self, source_url: str) -> Optional[Opportunity]:
        table = self.db.query(OpportunityTable).filter(OpportunityTable.source_url == source_url).first()
        return self._to_model(table) if table else None

    def search(
        self,
        query: Optional[str] = None,
        organization_type: Optional[str] = None,
        organization_level: Optional[str] = None,
        domain: Optional[str] = None,
        country: Optional[str] = None,
        opportunity_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Opportunity], int]:
        """Search opportunities with filters and pagination."""
        q = self.db.query(OpportunityTable)

        # Default rule: only show VERIFIED_OFFICIAL records unless specified
        q = q.filter(OpportunityTable.verification_status == VerificationStatus.VERIFIED_OFFICIAL.value)

        if query:
            search_pattern = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    OpportunityTable.title.ilike(search_pattern),
                    OpportunityTable.problem_statement.ilike(search_pattern),
                    OpportunityTable.organization_name.ilike(search_pattern),
                    OpportunityTable.domains.ilike(search_pattern)
                )
            )

        if organization_type:
            q = q.filter(OpportunityTable.organization_type == organization_type.lower())

        if organization_level:
            q = q.filter(OpportunityTable.organization_level == organization_level.lower())

        if domain:
            q = q.filter(OpportunityTable.domains.ilike(f"%{domain.lower()}%"))

        if country:
            q = q.filter(OpportunityTable.country.ilike(f"%{country}%"))

        if opportunity_type:
            q = q.filter(OpportunityTable.opportunity_type == opportunity_type.lower())

        if status:
            q = q.filter(OpportunityTable.status == status.upper())

        total = q.count()
        offset = (page - 1) * page_size
        results = q.order_by(OpportunityTable.first_seen_at.desc()).offset(offset).limit(page_size).all()

        return [self._to_model(r) for r in results], total

    def save(self, opp: Opportunity) -> Opportunity:
        """Create or update opportunity with automatic versioning."""
        existing = self.db.query(OpportunityTable).filter(OpportunityTable.id == opp.id).first()
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if not existing:
            # Create new record
            table = self._to_table(opp)
            table.first_seen_at = now
            table.last_verified_at = now
            self.db.add(table)
            self.db.commit()
            self.db.refresh(table)

            # Record Version 1 snapshot
            self._record_version(
                opp_id=table.id,
                version_number=1,
                reason="initial_discovery",
                diffs=[],
                snapshot=opp.model_dump(mode="json")
            )
            return self._to_model(table)

        # Record exists: Detect diffs for versioning
        diffs: List[FieldDiff] = []
        if existing.deadline != opp.deadline:
            diffs.append(FieldDiff(field_name="deadline", old_value=existing.deadline, new_value=opp.deadline))
        if existing.status != opp.status.value:
            diffs.append(FieldDiff(field_name="status", old_value=existing.status, new_value=opp.status.value))
        if existing.prize_amount != (opp.prize.amount if opp.prize else None):
            diffs.append(FieldDiff(field_name="prize_amount", old_value=existing.prize_amount, new_value=opp.prize.amount if opp.prize else None))

        if diffs:
            # Increment version
            new_version = existing.version + 1
            existing.version = new_version
            existing.last_changed_at = now
            self._record_version(
                opp_id=existing.id,
                version_number=new_version,
                reason="source_update",
                diffs=diffs,
                snapshot=opp.model_dump(mode="json")
            )

        # Update mutable fields
        existing.title = opp.title
        existing.problem_statement = opp.problem_statement
        existing.organization_name = opp.organization.name
        existing.status = opp.status.value
        existing.deadline = opp.deadline
        if opp.prize:
            existing.prize_amount = opp.prize.amount
            existing.prize_raw = opp.prize.raw_text
        existing.support_description = opp.support
        existing.domains = json.dumps(opp.domains)
        existing.eligibility = json.dumps(opp.eligibility)
        existing.requirements = json.dumps(opp.requirements)
        existing.last_verified_at = now

        evidence_dicts = [e.model_dump(mode="json") for e in opp.source_evidence]
        existing.source_evidence = json.dumps(evidence_dicts)

        self.db.commit()
        self.db.refresh(existing)
        return self._to_model(existing)

    def _record_version(self, opp_id: str, version_number: int, reason: str, diffs: List[FieldDiff], snapshot: Dict[str, Any]):
        version_entry = VersionTable(
            opportunity_id=opp_id,
            version_number=version_number,
            changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            change_reason=reason,
            diffs=json.dumps([d.model_dump() for d in diffs]),
            snapshot=json.dumps(snapshot)
        )
        self.db.add(version_entry)
        self.db.commit()

    def get_versions(self, opp_id: str) -> List[OpportunityVersion]:
        rows = (
            self.db.query(VersionTable)
            .filter(VersionTable.opportunity_id == opp_id)
            .order_by(VersionTable.version_number.asc())
            .all()
        )
        versions = []
        for r in rows:
            diff_dicts = json.loads(r.diffs) if r.diffs else []
            versions.append(
                OpportunityVersion(
                    version_number=r.version_number,
                    opportunity_id=r.opportunity_id,
                    changed_at=r.changed_at,
                    change_reason=r.change_reason,
                    diffs=[FieldDiff(**d) for d in diff_dicts],
                    snapshot=json.loads(r.snapshot) if r.snapshot else {}
                )
            )
        return versions

    def get_active_opportunities(self) -> List[Opportunity]:
        """Fetch all opportunities currently marked ACTIVE for monitoring."""
        rows = self.db.query(OpportunityTable).filter(OpportunityTable.status == OpportunityStatus.ACTIVE.value).all()
        return [self._to_model(r) for r in rows]
