from src.models.source import VerificationStatus
from src.services.verification import VerificationService
from src.sources.base import AuthorityEvidence, RawSource


def test_verify_official_government_source():
    service = VerificationService()
    raw = RawSource(
        url="https://innovateindia.mygov.in/challenges/test-challenge",
        final_url="https://innovateindia.mygov.in/challenges/test-challenge",
        status_code=200,
        content_type="text/html",
        text_content="Official challenge content",
        document_hash="dummy_hash"
    )
    status, reason = service.verify_source(raw)
    assert status == VerificationStatus.VERIFIED_OFFICIAL
    assert "authoritative official government source" in reason


def test_reject_secondary_media_source():
    service = VerificationService()
    raw = RawSource(
        url="https://medium.com/@user/government-seeking-startups",
        final_url="https://medium.com/@user/government-seeking-startups",
        status_code=200,
        content_type="text/html",
        text_content="Blog post discussing government challenges",
        document_hash="dummy_hash"
    )
    status, reason = service.verify_source(raw)
    assert status == VerificationStatus.REJECTED
    assert "secondary or media domain" in reason


def test_unknown_domain_needs_review():
    service = VerificationService()
    raw = RawSource(
        url="https://some-partner-portal.org/challenge",
        final_url="https://some-partner-portal.org/challenge",
        status_code=200,
        content_type="text/html",
        text_content="Challenge page",
        document_hash="dummy_hash"
    )
    status, reason = service.verify_source(raw)
    assert status == VerificationStatus.NEEDS_REVIEW
