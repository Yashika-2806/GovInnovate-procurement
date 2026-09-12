import pytest
from backend.graph import evaluator_graph
from backend.state import EvaluatorState

def test_software_milestone_pass_flow():
    """Test full LangGraph execution for a Software project with strong evidence."""
    initial_state = {
        "startup_profile": {
            "startup_id": "start-sw-1",
            "startup_name": "MediAI Diagnostics",
            "primary_domain": "Healthcare AI",
            "initial_pitch_score": 92.0,
            "demonstrated_execution_score": 0.0,
            "domain_relevance_vector": {}
        },
        "problem_definition": {
            "title": "Automated Mammography Screening AI",
            "awarded_domain": "Healthcare AI"
        },
        "current_milestone": {
            "id": "m1-proto",
            "title": "AI Model Prototype & API Integration",
            "project_type": "Software",
            "sequence_index": 1,
            "objective": "Build validated inference API with >= 90% accuracy and test coverage",
            "requirements": ["GitHub repo with CI/CD", "Automated test suite", "API documentation"],
            "kpis": [
                {"id": "kpi-1", "name": "Inference Latency", "target_value": 200, "actual_value": 150, "unit": "ms", "weight": 1.0, "achieved": True}
            ],
            "acceptance_criteria": ["CI/CD passing", "Test coverage >= 70%"],
            "contractual_approval_required": False,
            "contractual_approval_granted": False,
            "status": "Pending"
        },
        "submitted_evidence": [
            {
                "id": "ev-github-1",
                "evidence_type": "github_repo",
                "source": "https://github.com/mediai/mammography-ai",
                "timestamp": "2026-09-10T10:00:00Z",
                "verification_level": "System-generated",
                "relationship_to_milestone": "GitHub repo with CI/CD, Automated test suite, API documentation",
                "relevant_claim": "Full repo with CI/CD, 85% test coverage, FastAPI documentation",
                "content_payload": {
                    "commit_count": 42,
                    "merged_prs_count": 12,
                    "ci_cd_status": "SUCCESS",
                    "test_coverage_percent": 88.5,
                    "readme_present": True,
                    "api_docs_present": True,
                    "Inference Latency": 150
                }
            }
        ],
        "scoring_weights": {
            "requirement_completion": 0.30,
            "kpi_achievement": 0.20,
            "technical_quality": 0.20,
            "evidence_quality": 0.15,
            "testing_validation": 0.15,
            "documentation": 0.0,
            "practicality": 0.0,
            "delivery_timeliness": 0.0,
            "pass_threshold": 75.0
        },
        "audit_logs": []
    }

    config = {"configurable": {"thread_id": "test-thread-sw"}}
    result = evaluator_graph.invoke(initial_state, config=config)

    assert result["status"] == "Passed"
    assert result["milestone_score"]["total_weighted_score"] >= 75.0
    assert result["milestone_score"]["passed"] is True
    assert "Passed" in result["recommended_action"]
    assert len(result["audit_logs"]) >= 6
    assert result["startup_profile"]["demonstrated_execution_score"] > 0.0
    assert "Healthcare AI" in result["startup_profile"]["domain_relevance_vector"]


def test_contractual_approval_block_flow():
    """Test LangGraph conditional edge routing when contractual approval is missing."""
    initial_state = {
        "startup_profile": {
            "startup_id": "start-hw-1",
            "startup_name": "AeroSense Robotics",
            "primary_domain": "Industrial IoT",
            "initial_pitch_score": 85.0,
            "demonstrated_execution_score": 0.0,
            "domain_relevance_vector": {}
        },
        "current_milestone": {
            "id": "m-pilot",
            "title": "Production Deployment & Flight Pilot",
            "project_type": "Hardware",
            "sequence_index": 4,
            "objective": "Deploy 10 drone units in field",
            "requirements": ["10 units deployed"],
            "kpis": [],
            "acceptance_criteria": ["Independent audit report"],
            "contractual_approval_required": True,
            "contractual_approval_granted": False,  # Missing human approval
            "status": "Pending"
        },
        "submitted_evidence": [],
        "scoring_weights": {},
        "audit_logs": []
    }

    config = {"configurable": {"thread_id": "test-thread-1"}}
    result = evaluator_graph.invoke(initial_state, config=config)

    assert result["status"] == "Blocked"
    assert result["human_approval_required"] is True
    assert result["human_approval_granted"] is False
    assert "contractual obligations" in result["recommended_action"].lower()


def test_dummy_evidence_remediation_flow():
    """Test detection of dummy skeletal repo and weak physical evidence triggering Remediation status."""
    initial_state = {
        "startup_profile": {
            "startup_id": "start-sw-2",
            "startup_name": "QuickApp Inc",
            "primary_domain": "Fintech",
            "initial_pitch_score": 70.0,
            "demonstrated_execution_score": 0.0,
            "domain_relevance_vector": {}
        },
        "current_milestone": {
            "id": "m1-dummy",
            "title": "Payment Gateway Integration",
            "project_type": "Software",
            "sequence_index": 1,
            "objective": "Build secure payment microservice",
            "requirements": ["Payment gateway endpoint", "PCI DSS security report"],
            "kpis": [],
            "acceptance_criteria": ["Passing tests"],
            "contractual_approval_required": False,
            "contractual_approval_granted": False,
            "status": "Pending"
        },
        "submitted_evidence": [
            {
                "id": "ev-dummy-1",
                "evidence_type": "github_repo",
                "source": "https://github.com/quickapp/template-repo",
                "timestamp": "2026-09-10T10:00:00Z",
                "verification_level": "Self-reported",
                "relationship_to_milestone": "Payment gateway endpoint",
                "relevant_claim": "Repo uploaded",
                "content_payload": {
                    "commit_count": 1,
                    "merged_prs_count": 0,
                    "is_template_repo_only": True,
                    "ci_cd_status": "NONE",
                    "test_coverage_percent": 0.0
                }
            }
        ],
        "scoring_weights": {"pass_threshold": 75.0},
        "audit_logs": []
    }

    config = {"configurable": {"thread_id": "test-thread-dummy"}}
    result = evaluator_graph.invoke(initial_state, config=config)

    assert result["status"] in ["Requires Remediation", "Failed"]
    assert len(result["evidence_analysis"]["uncertainty_flags"]) > 0
    assert result["milestone_score"]["total_weighted_score"] < 75.0
