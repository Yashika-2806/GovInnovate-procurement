from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskLevel(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    EXTREME = "EXTREME"
    NEGLIGIBLE = "NEGLIGIBLE"


class RiskCategory(str, Enum):
    PROBLEM = "PROBLEM"
    MARKET = "MARKET"
    PMF = "PMF"
    COMPETITION = "COMPETITION"
    BUSINESS_MODEL = "BUSINESS_MODEL"
    FINANCIAL = "FINANCIAL"
    TECHNOLOGY = "TECHNOLOGY"
    REGULATORY = "REGULATORY"
    OPERATIONAL = "OPERATIONAL"
    TEAM = "TEAM"
    FUNDING = "FUNDING"
    MACRO = "MACRO"


class SubFactorScore(BaseModel):
    name: str = ""
    score: float = 50.0
    evidence: List[str] = []
    confidence: str = "MEDIUM"


class RiskCategoryScore(BaseModel):
    category: str = ""
    score: float = 50.0
    confidence: str = "MEDIUM"
    sub_factors: List[SubFactorScore] = []
    explanation: str = ""
    evidence: List[str] = []
    comparable_failures: List[str] = []
    impact: str = ""
    impact_description: str = ""
    probability: str = ""
    probability_estimate: str = ""
    mitigation: str = ""
    mitigation_suggestions: List[str] = []


class WeightedScore(BaseModel):
    category: str = ""
    raw_score: float = 0.0
    weight: float = 0.0
    weighted_score: float = 0.0


class RiskMatrixItem(BaseModel):
    risk_name: str = ""
    probability: int = 3
    impact: int = 3
    severity: str = "Medium"
    score: float = 50.0


class SimilarCompany(BaseModel):
    company_name: str = ""
    similarity_score: float = 0.0
    similarity_factors: List[str] = []
    factors: List[str] = []
    outcome: str = "FAILED"
    key_comparison_points: List[str] = []


class CumulativeRiskAssessment(BaseModel):
    category_scores: List[RiskCategoryScore] = []
    weighted_scores: List[WeightedScore] = []
    cumulative_score: float = 0.0
    overall_score: float = 0.0
    risk_level: str = "MODERATE"
    risk_matrix: List[RiskMatrixItem] = []
    top_risks: List[str] = []
    top_strengths: List[str] = []
    key_unknowns: List[str] = []
