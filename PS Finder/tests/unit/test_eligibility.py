from src.services.eligibility import EligibilityClassifier


def test_qualify_solution_seeking_challenge():
    classifier = EligibilityClassifier()
    title = "AI Innovation Challenge: Autonomous Traffic Management"
    content = "The department is seeking innovative problem statement solutions from tech startups to build a proof of concept pilot."

    status, reason = classifier.classify(content, title)
    assert status == "QUALIFIED"
    assert "Explicit solution-seeking challenge" in reason


def test_reject_routine_procurement_cctv():
    classifier = EligibilityClassifier()
    title = "Tender for Supply 500 standard CCTV cameras"
    content = "Department invites tenders for the purchase of 500 standard CCTV cameras with 3 years warranty."

    status, reason = classifier.classify(content, title)
    assert status == "REJECTED"
    assert "Routine procurement detected" in reason


def test_reject_annual_maintenance_contract():
    classifier = EligibilityClassifier()
    title = "Annual Maintenance Contract for Office Air Conditioners"
    content = "Tender for AMC for air conditioners across headquarters building."

    status, reason = classifier.classify(content, title)
    assert status == "REJECTED"
