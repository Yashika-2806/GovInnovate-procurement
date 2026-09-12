from unittest.mock import MagicMock
from src.models.opportunity import Opportunity, OpportunityStatus, OpportunityType
from src.models.organization import Organization, OrganizationType
from src.models.source import SourceInfo, VerificationStatus
from src.services.dedup import DeduplicationService


def _create_opp(opp_id: str, title: str, org_name: str, url: str) -> Opportunity:
    return Opportunity(
        id=opp_id,
        title=title,
        problem_statement="Problem statement details",
        organization=Organization(name=org_name, type=OrganizationType.GOVERNMENT),
        opportunity_type=OpportunityType.INNOVATION_CHALLENGE,
        domains=["smart_cities"],
        status=OpportunityStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source=SourceInfo(
            url=url,
            source_domain="startupindia.gov.in",
            issuing_organization=org_name
        )
    )


def test_detect_exact_duplicate_by_url():
    mock_repo = MagicMock()
    service = DeduplicationService(mock_repo)

    opp1 = _create_opp("opp_1", "Smart Waste Challenge", "MoHUA", "https://startupindia.gov.in/waste1")
    opp2 = _create_opp("opp_2", "Smart Waste Challenge", "MoHUA", "https://startupindia.gov.in/waste1")

    is_exact, dup_id, decision = service.check_duplicate(opp2, [opp1])
    assert is_exact is True
    assert dup_id == "opp_1"
    assert decision == "EXACT_DUPLICATE"


def test_flag_uncertain_duplicate_as_needs_review():
    mock_repo = MagicMock()
    service = DeduplicationService(mock_repo)

    opp1 = _create_opp("opp_1", "National IoT Water Monitoring Challenge", "Ministry of Jal Shakti", "https://startupindia.gov.in/water1")
    # Very similar title, different URL
    opp2 = _create_opp("opp_2", "National IoT Water Quality Monitoring Challenge", "State Water Board", "https://jalshakti.gov.in/water-challenge")

    is_exact, dup_id, decision = service.check_duplicate(opp2, [opp1])
    assert is_exact is False
    assert dup_id == "opp_1"
    assert decision == "NEEDS_REVIEW"


def test_unique_opportunity():
    mock_repo = MagicMock()
    service = DeduplicationService(mock_repo)

    opp1 = _create_opp("opp_1", "Smart Waste Challenge", "MoHUA", "https://startupindia.gov.in/waste1")
    opp2 = _create_opp("opp_2", "Quantum Encryption Security Challenge", "MeitY", "https://mygov.in/quantum")

    is_exact, dup_id, decision = service.check_duplicate(opp2, [opp1])
    assert is_exact is False
    assert dup_id is None
    assert decision == "UNIQUE"
