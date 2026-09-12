from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# Milestone Evaluation Statuses
MilestoneStatus = Literal[
    "Pending",
    "In Progress",
    "Submitted",
    "Under Review",
    "Passed",
    "Failed",
    "Requires Remediation",
    "Blocked"
]

# Evidence Verification Levels
VerificationLevel = Literal[
    "Self-reported",
    "System-generated",
    "Third-party",
    "Independently verified"
]

# Project Types
ProjectType = Literal["Software", "Hardware", "Hybrid"]

# Evidence Models
class EvidenceItem(BaseModel):
    id: str
    evidence_type: str
    source: str
    timestamp: str
    verification_level: VerificationLevel
    relationship_to_milestone: str
    relevant_claim: str
    content_payload: Dict[str, Any]  # Stores metrics, repo metadata, telemetry points, inspection logs
    is_valid_structure: bool = True
    uncertainty_score: float = 0.0  # 0.0 (certain) to 1.0 (highly uncertain/unverified)
    analysis_notes: str = ""

# KPI Model
class KPI(BaseModel):
    id: str
    name: str
    target_value: float
    actual_value: Optional[float] = None
    unit: str
    weight: float = 1.0
    achieved: bool = False

# Milestone Model
class Milestone(BaseModel):
    id: str
    title: str
    project_type: ProjectType
    sequence_index: int
    objective: str
    requirements: List[str]
    kpis: List[KPI]
    acceptance_criteria: List[str]
    contractual_approval_required: bool = False
    contractual_approval_granted: bool = False
    status: MilestoneStatus = "Pending"

# Configurable Weighted Scoring Criteria
class ScoringWeights(BaseModel):
    requirement_completion: float = 0.25
    kpi_achievement: float = 0.20
    technical_quality: float = 0.15
    evidence_quality: float = 0.15
    testing_validation: float = 0.10
    documentation: float = 0.05
    practicality: float = 0.05
    delivery_timeliness: float = 0.05
    pass_threshold: float = 75.0  # Out of 100

# Milestone Score Model
class MilestoneScore(BaseModel):
    requirement_completion_score: float = 0.0
    kpi_achievement_score: float = 0.0
    technical_quality_score: float = 0.0
    evidence_quality_score: float = 0.0
    testing_validation_score: float = 0.0
    documentation_score: float = 0.0
    practicality_score: float = 0.0
    delivery_timeliness_score: float = 0.0
    total_weighted_score: float = 0.0
    passed: bool = False

# Startup Performance Profile Model
class ContextualPerformanceProfile(BaseModel):
    startup_id: str
    startup_name: str
    primary_domain: str  # e.g., Healthcare, AI/ML, Industrial IoT, CleanTech, Fintech
    secondary_domains: List[str] = []
    initial_pitch_score: float  # Initial capability from pitch
    demonstrated_execution_score: float  # Calculated strictly from actual milestone execution
    historical_milestones_completed: int = 0
    historical_milestones_failed: int = 0
    on_time_delivery_rate: float = 1.0  # 0.0 to 1.0
    average_evidence_quality: float = 0.0
    domain_relevance_vector: Dict[str, float] = {}  # Domain -> demonstrated competence score

# Escrow Disbursement Model
class EscrowDisbursement(BaseModel):
    tranche_amount_usd: float = 50000.0
    penalty_deduction_usd: float = 0.0
    net_payout_usd: float = 50000.0
    escrow_status: Literal["Locked", "Approved", "Disbursed", "Withheld"] = "Locked"
    disbursement_notes: str = ""

# Security Audit Model
class SecurityAudit(BaseModel):
    vulnerability_score: float = 90.0  # 0 to 100
    critical_cve_count: int = 0
    dependency_freshness_score: float = 85.0
    security_passed: bool = True

# Telemetry Anomaly Model
class TelemetryAnomaly(BaseModel):
    telemetry_consistency_percent: float = 98.5
    gps_spoofing_risk: float = 0.05  # 0.0 to 1.0
    anomaly_detected: bool = False
    notes: str = ""

# Human Auditor Override Model
class HumanOverride(BaseModel):
    auditor_id: Optional[str] = None
    auditor_notes: Optional[str] = None
    override_score_adjustment: float = 0.0
    force_status: Optional[MilestoneStatus] = None

# Audit Log Entry
class AuditLogEntry(BaseModel):
    timestamp: str
    node_name: str
    event: str
    details: str
    uncertainty_alert: Optional[str] = None

# LangGraph TypedDict State
class EvaluatorState(TypedDict):
    startup_profile: Dict[str, Any]
    problem_definition: Dict[str, Any]
    current_milestone: Dict[str, Any]
    multi_milestone_track: List[Dict[str, Any]]
    submitted_evidence: List[Dict[str, Any]]
    scoring_weights: Dict[str, Any]
    evidence_analysis: Dict[str, Any]
    security_audit: Dict[str, Any]
    telemetry_anomaly: Dict[str, Any]
    milestone_score: Dict[str, Any]
    escrow_disbursement: Dict[str, Any]
    justification_report: Dict[str, Any]
    human_override: Dict[str, Any]
    status: MilestoneStatus
    recommended_action: str
    human_approval_required: bool
    human_approval_granted: bool
    audit_logs: List[Dict[str, Any]]
    execution_step: str

