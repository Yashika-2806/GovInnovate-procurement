from enum import Enum
from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

class InfoSource(str, Enum):
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    MISSING = "MISSING"

class CustomerType(str, Enum):
    B2B = "B2B"
    B2C = "B2C"
    B2B2C = "B2B2C"
    B2G = "B2G"
    OTHER = "OTHER"

T = TypeVar('T')

class FieldWithSource(BaseModel, Generic[T]):
    value: Optional[T] = None
    source: InfoSource = InfoSource.MISSING

class StartupProfile(BaseModel):
    industry: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    sub_industry: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    target_customers: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    customer_type: FieldWithSource[CustomerType] = Field(default_factory=FieldWithSource)
    problem_description: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    solution_description: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    technology: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    business_model: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    revenue_model: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    geographic_market: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    regulatory_environment: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    capital_requirements: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    operational_complexity: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    competitors: FieldWithSource[List[str]] = Field(default_factory=FieldWithSource)
    key_dependencies: FieldWithSource[List[str]] = Field(default_factory=FieldWithSource)
    scalability: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    severity_of_problem: FieldWithSource[str] = Field(default_factory=FieldWithSource)
    existing_alternatives: FieldWithSource[List[str]] = Field(default_factory=FieldWithSource)

class MissingInfoReport(BaseModel):
    missing_fields: List[str]
    suggested_questions: List[str]
