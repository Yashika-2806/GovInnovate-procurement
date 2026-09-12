"""Tests for Pitch Evaluator configuration system."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from pitch_evaluator.config import (
    ConfigLoader,
    CriterionConfig,
    EvaluationCriteriaConfig,
    load_criteria_config,
)


class TestCriterionConfig:
    """Tests for CriterionConfig model."""

    def test_valid_criterion(self) -> None:
        criterion = CriterionConfig(
            name="Test Criterion",
            weight=0.5,
            enabled=True,
            description="A test criterion",
            evidence_guidance="Look for test evidence",
        )
        assert criterion.name == "Test Criterion"
        assert criterion.weight == 0.5
        assert criterion.enabled is True

    def test_invalid_negative_weight(self) -> None:
        with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
            CriterionConfig(
                name="Test",
                weight=-0.1,
                enabled=True,
                description="desc",
                evidence_guidance="guidance",
            )

    def test_invalid_weight_above_one(self) -> None:
        with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
            CriterionConfig(
                name="Test",
                weight=1.5,
                enabled=True,
                description="desc",
                evidence_guidance="guidance",
            )

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            CriterionConfig(
                name="",
                weight=0.5,
                enabled=True,
                description="desc",
                evidence_guidance="guidance",
            )

    def test_empty_description_rejected(self) -> None:
        with pytest.raises(ValueError):
            CriterionConfig(
                name="Test",
                weight=0.5,
                enabled=True,
                description="",
                evidence_guidance="guidance",
            )

    def test_empty_evidence_guidance_rejected(self) -> None:
        with pytest.raises(ValueError):
            CriterionConfig(
                name="Test",
                weight=0.5,
                enabled=True,
                description="desc",
                evidence_guidance="",
            )


class TestEvaluationCriteriaConfig:
    """Tests for EvaluationCriteriaConfig model."""

    def _base_config_data(self) -> dict:
        return {
            "version": "1.0",
            "criteria": [
                {
                    "name": "Criterion A",
                    "weight": 0.6,
                    "enabled": True,
                    "description": "First criterion",
                    "evidence_guidance": "guidance a",
                },
                {
                    "name": "Criterion B",
                    "weight": 0.4,
                    "enabled": True,
                    "description": "Second criterion",
                    "evidence_guidance": "guidance b",
                },
            ],
        }

    def test_valid_config_loads(self) -> None:
        config = EvaluationCriteriaConfig.model_validate(self._base_config_data())
        assert config.version == "1.0"
        assert len(config.criteria) == 2
        assert config.get_enabled_criteria() == config.criteria

    def test_duplicate_names_rejected(self) -> None:
        data = self._base_config_data()
        data["criteria"].append(
            {
                "name": "Criterion A",  # duplicate
                "weight": 0.1,
                "enabled": True,
                "description": "Duplicate",
                "evidence_guidance": "guidance",
            }
        )
        with pytest.raises(ValueError, match="Duplicate criterion names"):
            EvaluationCriteriaConfig.model_validate(data)

    def test_weights_not_summing_to_one_rejected(self) -> None:
        data = self._base_config_data()
        data["criteria"][0]["weight"] = 0.5  # total = 0.9
        with pytest.raises(ValueError, match="must sum to 1.0"):
            EvaluationCriteriaConfig.model_validate(data)

    def test_enabled_criterion_with_zero_weight_rejected(self) -> None:
        data = self._base_config_data()
        # Keep sum valid: A=0.0, B=1.0 -> sum=1.0, but A has zero weight while enabled
        data["criteria"][0]["weight"] = 0.0
        data["criteria"][1]["weight"] = 1.0
        with pytest.raises(ValueError, match="must have weight > 0"):
            EvaluationCriteriaConfig.model_validate(data)

    def test_disabled_criterion_can_have_zero_weight(self) -> None:
        data = self._base_config_data()
        data["criteria"].append(
            {
                "name": "Criterion C",
                "weight": 0.0,
                "enabled": False,
                "description": "Disabled",
                "evidence_guidance": "guidance",
            }
        )
        # Adjust weights to sum to 1.0
        data["criteria"][0]["weight"] = 0.6
        data["criteria"][1]["weight"] = 0.4
        config = EvaluationCriteriaConfig.model_validate(data)
        assert len(config.get_enabled_criteria()) == 2

    def test_missing_version_rejected(self) -> None:
        data = self._base_config_data()
        del data["version"]
        with pytest.raises(ValueError):
            EvaluationCriteriaConfig.model_validate(data)

    def test_empty_version_rejected(self) -> None:
        data = self._base_config_data()
        data["version"] = ""
        with pytest.raises(ValueError):
            EvaluationCriteriaConfig.model_validate(data)

    def test_missing_required_fields_rejected(self) -> None:
        data = self._base_config_data()
        data["criteria"][0].pop("description")
        with pytest.raises(ValueError):
            EvaluationCriteriaConfig.model_validate(data)

    def test_no_enabled_criteria_rejected(self) -> None:
        data = self._base_config_data()
        data["criteria"][0]["enabled"] = False
        data["criteria"][1]["enabled"] = False
        with pytest.raises(ValueError, match="At least one criterion must be enabled"):
            EvaluationCriteriaConfig.model_validate(data)

    def test_get_criterion_weight(self) -> None:
        config = EvaluationCriteriaConfig.model_validate(self._base_config_data())
        assert config.get_criterion_weight("Criterion A") == 0.6
        assert config.get_criterion_weight("Criterion B") == 0.4

    def test_get_criterion_weight_missing_raises(self) -> None:
        config = EvaluationCriteriaConfig.model_validate(self._base_config_data())
        with pytest.raises(KeyError):
            config.get_criterion_weight("NonExistent")

    def test_get_enabled_criteria_sorted(self) -> None:
        data = self._base_config_data()
        # Add in non-alphabetical order
        data["criteria"].insert(
            0,
            {
                "name": "Zebra Criterion",
                "weight": 0.1,
                "enabled": True,
                "description": "Z criterion",
                "evidence_guidance": "guidance",
            }
        )
        data["criteria"][1]["weight"] = 0.5  # A = 0.5
        data["criteria"][2]["weight"] = 0.4  # B = 0.4
        config = EvaluationCriteriaConfig.model_validate(data)
        enabled = config.get_enabled_criteria()
        names = [c.name for c in enabled]
        assert names == ["Criterion A", "Criterion B", "Zebra Criterion"]


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_loads_valid_yaml(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "version": "1.0",
                    "criteria": [
                        {
                            "name": "Test A",
                            "weight": 0.5,
                            "enabled": True,
                            "description": "A",
                            "evidence_guidance": "a",
                        },
                        {
                            "name": "Test B",
                            "weight": 0.5,
                            "enabled": True,
                            "description": "B",
                            "evidence_guidance": "b",
                        },
                    ],
                },
                f,
            )
            path = Path(f.name)

        try:
            loader = ConfigLoader(config_path=path)
            config = loader.load()
            assert config.version == "1.0"
            assert len(config.criteria) == 2
        finally:
            path.unlink()

    def test_file_not_found_raises(self) -> None:
        loader = ConfigLoader(config_path=Path("/nonexistent/path.yaml"))
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_empty_file_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            path = Path(f.name)

        try:
            loader = ConfigLoader(config_path=path)
            with pytest.raises(ValueError, match="empty"):
                loader.load()
        finally:
            path.unlink()

    def test_invalid_yaml_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: [unclosed")
            path = Path(f.name)

        try:
            loader = ConfigLoader(config_path=path)
            with pytest.raises(yaml.YAMLError):
                loader.load()
        finally:
            path.unlink()


class TestDefaultConfig:
    """Tests using the actual default configuration file."""

    def test_default_config_loads(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        assert config.version == "1.0"
        assert len(config.criteria) == 15

    def test_default_config_weights_sum_to_one(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        enabled = config.get_enabled_criteria()
        total = sum(c.weight for c in enabled)
        assert abs(total - 1.0) < 1e-9

    def test_core_criteria_present_and_enabled(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        core_names = {
            "Problem Validation",
            "Scalability",
            "Feasibility",
            "Cost",
            "Practicality",
        }
        enabled_names = {c.name for c in config.get_enabled_criteria()}
        assert core_names.issubset(enabled_names)

    def test_core_criteria_weights_match_spec(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        expected = {
            "Problem Validation": 0.20,
            "Scalability": 0.15,
            "Feasibility": 0.15,
            "Cost": 0.15,
            "Practicality": 0.10,
        }
        for name, expected_weight in expected.items():
            actual = config.get_criterion_weight(name)
            assert actual == expected_weight, f"{name}: expected {expected_weight}, got {actual}"

    def test_evidence_quality_is_disabled(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        eq = next(c for c in config.criteria if c.name == "Evidence Quality")
        assert eq.enabled is False
        assert eq.weight == 0.0  # disabled criteria have zero weight

    def test_all_criteria_have_descriptions_and_guidance(self) -> None:
        config = load_criteria_config(Path("config/evaluation_criteria.yaml"))
        for c in config.criteria:
            assert c.description.strip(), f"Missing description for {c.name}"
            assert c.evidence_guidance.strip(), f"Missing evidence_guidance for {c.name}"