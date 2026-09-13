from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .startup_profile import StartupProfile
from .risk_scores import CumulativeRiskAssessment, WeightedScore, RiskCategory, SimilarCompany
from .research_data import FailedStartup, SuccessfulStartup, Citation, ResearchResults


class MitigationStrategy(BaseModel):
    risk_name: str = ""
    risk_category: str = ""
    why_it_matters: str = ""
    evidence: List[str] = []
    recommended_action: str = ""
    strategy: str = ""
    expected_impact: str = ""
    difficulty: str = "MEDIUM"
    impact: str = "HIGH"


class DataQuality(BaseModel):
    missing_data: List[str] = []
    dataset_size: int = 0
    assumptions: List[str] = []
    confidence_levels: Dict[str, str] = {}
    potential_biases: List[str] = []
    limitations: List[str] = []


class ExecutiveSummary(BaseModel):
    cumulative_score: float = 0.0
    overall_score: float = 0.0
    overall_risk_level: str = "MODERATE"
    risk_classification: str = ""
    top_5_risks: List[str] = []
    top_risks: List[str] = []
    top_5_strengths: List[str] = []
    key_strengths: List[str] = []
    key_unknowns: List[str] = []
    critical_warnings: List[str] = []
    recommendation: str = ""


class FullReport(BaseModel):
    executive_summary: ExecutiveSummary
    startup_overview: Optional[StartupProfile] = None
    profile: Optional[StartupProfile] = None
    risk_assessment: CumulativeRiskAssessment
    research_data: Optional[ResearchResults] = None
    historical_failures: List[FailedStartup] = []
    successful_benchmarks: List[SuccessfulStartup] = []
    statistical_findings: Dict[str, Any] = {}
    statistical_insights: Dict[str, Any] = {}
    comparable_companies: List[SimilarCompany] = []
    similar_companies: List[SimilarCompany] = []
    score_calculation: List[WeightedScore] = []
    key_risk_drivers: List[str] = []
    mitigation_strategies: List[MitigationStrategy] = []
    data_quality: Optional[DataQuality] = None
    data_quality_assessment: str = ""
    sources: List[Citation] = []
    citations: List[str] = []
