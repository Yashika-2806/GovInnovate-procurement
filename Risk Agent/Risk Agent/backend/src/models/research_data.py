from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PRIMARY_DATA = "PRIMARY_DATA"
    SECONDARY_DATA = "SECONDARY_DATA"
    EXPERT_OPINION = "EXPERT_OPINION"
    AI_INFERENCE = "AI_INFERENCE"
    ASSUMPTION = "ASSUMPTION"


class Citation(BaseModel):
    url: str = ""
    title: str = ""
    source_type: SourceType = SourceType.SECONDARY_DATA
    snippet: str = ""
    accessed_date: str = ""


class FailureCause(str, Enum):
    LACK_OF_PMF = "LACK_OF_PMF"
    MARKET_TOO_SMALL = "MARKET_TOO_SMALL"
    POOR_EXECUTION = "POOR_EXECUTION"
    REGULATORY = "REGULATORY"
    HIGH_CAC = "HIGH_CAC"
    LOW_RETENTION = "LOW_RETENTION"
    CASH_FLOW = "CASH_FLOW"
    EXCESSIVE_BURN = "EXCESSIVE_BURN"
    COMPETITION = "COMPETITION"
    TECH_FAILURE = "TECH_FAILURE"
    PRICING = "PRICING"
    TEAM_ISSUES = "TEAM_ISSUES"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    LEGAL = "LEGAL"
    FRAUD = "FRAUD"
    MACRO = "MACRO"
    OTHER = "OTHER"


class FailedStartup(BaseModel):
    company_name: str = ""
    industry: str = ""
    founding_year: Optional[int] = None
    shutdown_year: Optional[int] = None
    location: Optional[str] = None
    business_model: Optional[str] = None
    target_customer: Optional[str] = None
    product_description: Optional[str] = None
    funding_raised: Optional[str] = None
    major_investors: List[str] = Field(default_factory=list)
    peak_valuation: Optional[str] = None
    employees: Optional[str] = None
    years_operated: Optional[int] = None
    failure_causes: List[FailureCause] = Field(default_factory=list)
    failure_narrative: str = ""
    what_happened: str = ""
    primary_cause: str = ""
    citations: List[str] = Field(default_factory=list)


class SuccessfulStartup(BaseModel):
    company_name: str = ""
    industry: str = ""
    founding_year: Optional[int] = None
    location: Optional[str] = None
    business_model: Optional[str] = None
    target_customer: Optional[str] = None
    product_description: Optional[str] = None
    funding_raised: Optional[str] = None
    major_investors: List[str] = Field(default_factory=list)
    current_valuation: Optional[str] = None
    revenue: Optional[str] = None
    employees: Optional[str] = None
    success_factors: List[str] = Field(default_factory=list)
    key_differentiators: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class IndustryResearch(BaseModel):
    industry_name: str = ""
    market_size: Optional[str] = None
    growth_rate: Optional[str] = None
    failure_rate: Optional[str] = None
    common_failure_patterns: List[str] = Field(default_factory=list)
    key_trends: List[str] = Field(default_factory=list)
    regulatory_landscape: Optional[str] = None
    citations: List[str] = Field(default_factory=list)


class MarketResearch(BaseModel):
    tam: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None
    growth_rate: Optional[str] = None
    maturity: Optional[str] = None
    concentration: Optional[str] = None
    key_players: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class RegulatoryResearch(BaseModel):
    regulations: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    approval_timelines: Optional[str] = None
    data_privacy: Optional[str] = None
    liability_issues: Optional[str] = None
    citations: List[str] = Field(default_factory=list)


class CompetitorData(BaseModel):
    name: str = ""
    description: str = ""
    funding: Optional[str] = None
    market_position: str = "Competitor"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class CompetitorResearch(BaseModel):
    direct_competitors: List[CompetitorData] = Field(default_factory=list)
    indirect_competitors: List[CompetitorData] = Field(default_factory=list)
    market_concentration: str = "Moderate"
    citations: List[str] = Field(default_factory=list)


class ResearchResults(BaseModel):
    industry: Optional[IndustryResearch] = None
    market: Optional[MarketResearch] = None
    failures: List[FailedStartup] = Field(default_factory=list)
    successes: List[SuccessfulStartup] = Field(default_factory=list)
    regulatory: Optional[RegulatoryResearch] = None
    competitors: Optional[CompetitorResearch] = None
    all_citations: List[Citation] = Field(default_factory=list)
