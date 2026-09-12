from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CriterionConfig(BaseModel):
    """Configuration for a single evaluation criterion."""

    name: Annotated[str, Field(min_length=1)]
    weight: Annotated[float, Field(ge=0.0, le=1.0)]
    enabled: bool = True
    description: Annotated[str, Field(min_length=1)]
    evidence_guidance: Annotated[str, Field(min_length=1)]

    @field_validator("weight", mode="before")
    @classmethod
    def _validate_weight(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v


class EvaluationCriteriaConfig(BaseModel):
    """Complete evaluation criteria configuration."""

    version: Annotated[str, Field(min_length=1)]
    criteria: Annotated[list[CriterionConfig], Field(min_length=1)]

    @field_validator("criteria", mode="after")
    @classmethod
    def _validate_unique_names(cls, criteria: list[CriterionConfig]) -> list[CriterionConfig]:
        names = [c.name for c in criteria]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate criterion names: {set(duplicates)}")
        return criteria

    @model_validator(mode="after")
    def _validate_weights_sum_to_one(self) -> EvaluationCriteriaConfig:
        enabled_criteria = [c for c in self.criteria if c.enabled]
        if not enabled_criteria:
            raise ValueError("At least one criterion must be enabled")

        total_weight = sum(c.weight for c in enabled_criteria)
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError(
                f"Enabled criteria weights must sum to 1.0, got {total_weight:.10f}. "
                f"Enabled criteria: {[c.name for c in enabled_criteria]}"
            )

        for c in enabled_criteria:
            if c.weight <= 0:
                raise ValueError(
                    f"Enabled criterion '{c.name}' must have weight > 0, got {c.weight}"
                )

        return self

    def get_enabled_criteria(self) -> list[CriterionConfig]:
        """Return only enabled criteria, sorted by name for consistency."""
        return sorted([c for c in self.criteria if c.enabled], key=lambda c: c.name)

    def get_criterion_weight(self, name: str) -> float:
        """Get weight for a specific criterion by name."""
        for c in self.criteria:
            if c.name == name:
                return c.weight
        raise KeyError(f"Criterion '{name}' not found in configuration")


class ConfigLoader(BaseSettings):
    """Loads and validates evaluation criteria configuration from YAML file."""

    model_config = SettingsConfigDict(
        env_prefix="PITCH_EVALUATOR_",
        case_sensitive=False,
    )

    config_path: Path = Path("config/evaluation_criteria.yaml")

    def load(self) -> EvaluationCriteriaConfig:
        """Load and validate configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ValueError("Configuration file is empty")

        return EvaluationCriteriaConfig.model_validate(data)


def load_criteria_config(path: Path | str | None = None) -> EvaluationCriteriaConfig:
    """Convenience function to load criteria configuration."""
    if path is not None:
        loader = ConfigLoader(config_path=Path(path))
    else:
        loader = ConfigLoader()
    return loader.load()