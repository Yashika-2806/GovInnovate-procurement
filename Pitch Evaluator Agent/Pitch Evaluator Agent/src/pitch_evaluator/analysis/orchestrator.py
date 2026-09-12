from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pitch_evaluator.analysis.engine import create_criterion_analysis_engine
from pitch_evaluator.config import EvaluationCriteriaConfig, load_criteria_config
from pitch_evaluator.evidence import EvidenceExtractionOutput, EvidenceExtractor
from pitch_evaluator.models import (
    CriterionAnalysis,
    EvaluationMetadata,
    EvidenceCitation,
    NormalizedPitch,
    PitchEvaluation,
    RiskSignals,
)


@dataclass
class AnalysisOutput:
    """Complete output from the analysis orchestrator."""

    criterion_analyses: list[CriterionAnalysis]
    pitch_evaluation: PitchEvaluation
    evidence_extraction_output: EvidenceExtractionOutput
    calculation_audit: list[dict[str, Any]] = field(default_factory=list)


class AnalysisOrchestrator:
    """High-level orchestrator for criterion analysis and pitch evaluation."""

    def __init__(
        self,
        engine: str = "mock",
        evidence_engine: str = "mock",
        criteria_config: EvaluationCriteriaConfig | str | None = None,
        **engine_kwargs: Any,
    ) -> None:
        """Initialize analysis orchestrator.

        Args:
            engine: Criterion analysis engine type ("mock" or "llm")
            evidence_engine: Evidence extraction engine type ("mock" or "llm")
            criteria_config: Evaluation criteria config or path to YAML
            **engine_kwargs: Additional engine configuration
        """
        # Load criteria config if path provided
        if isinstance(criteria_config, str):
            self._criteria_config = load_criteria_config(criteria_config)
        elif criteria_config is None:
            self._criteria_config = load_criteria_config()
        else:
            self._criteria_config = criteria_config

        # Initialize engines
        self._evidence_extractor = EvidenceExtractor(engine=evidence_engine)
        self._criterion_engine = create_criterion_analysis_engine(engine, **engine_kwargs)

    def evaluate(
        self,
        normalized_pitch: NormalizedPitch,
        pitch_id: str,
        startup_id: str,
        problem_statement_id: str,
    ) -> AnalysisOutput:
        """Run complete evaluation pipeline.

        Args:
            normalized_pitch: Normalized pitch from extraction layer
            pitch_id: Unique identifier for the pitch
            startup_id: Unique identifier for the startup
            problem_statement_id: Unique identifier for the problem statement

        Returns:
            AnalysisOutput with criterion analyses and final pitch evaluation
        """
        # Step 1: Extract evidence
        evidence_output = self._evidence_extractor.extract(
            normalized_pitch, self._criteria_config
        )

        # Step 2: Analyze each criterion
        criterion_analyses = self._analyze_all_criteria(
            normalized_pitch, evidence_output
        )

        # Step 3: Calculate deterministic weighted score
        weighted_total, criterion_scores, score_audit = calculate_weighted_score(
            criterion_analyses, self._criteria_config
        )

        # Step 4: Compute overall confidence (weighted average)
        overall_confidence = calculate_overall_confidence(
            criterion_analyses, self._criteria_config
        )

        # Step 5: Compute evidence quality
        evidence_quality = calculate_evidence_quality(
            evidence_citations=evidence_output.citations
        )

        # Step 6: Extract risk signals from analysis
        risk_signals = extract_risk_signals(criterion_analyses)

        # Step 7: Aggregate strengths, weaknesses, missing info, uncertainties
        all_strengths = []
        all_weaknesses = []
        all_missing = []
        all_uncertainties = []
        for analysis in criterion_analyses:
            all_strengths.extend(analysis.strengths)
            all_weaknesses.extend(analysis.weaknesses)
            all_missing.extend(analysis.missing_information)
            all_uncertainties.extend(analysis.uncertainties)

        # Step 8: Assemble final PitchEvaluation
        pitch_evaluation = PitchEvaluation(
            pitch_evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            pitch_id=pitch_id,
            startup_id=startup_id,
            problem_statement_id=problem_statement_id,
            criterion_scores=criterion_scores,
            weighted_total=weighted_total,
            evidence_citations=evidence_output.citations,
            strengths=all_strengths,
            weaknesses=all_weaknesses,
            missing_information=all_missing,
            uncertainties=all_uncertainties,
            risk_signals=risk_signals,
            confidence=overall_confidence,
            evidence_quality=evidence_quality,
            metadata=EvaluationMetadata(
                criteria_config_version=self._criteria_config.version,
                evaluator_version="0.1.0",
                processed_at=datetime.now(UTC),
                source_modality=normalized_pitch.source_modality.value,
                processing_time_ms=0,  # Could be measured
                llm_model=None,  # Set if using LLM
                criteria_used=[c.name for c in self._criteria_config.get_enabled_criteria()],
            ),
            calculation_audit=score_audit,
        )

        return AnalysisOutput(
            criterion_analyses=criterion_analyses,
            pitch_evaluation=pitch_evaluation,
            evidence_extraction_output=evidence_output,
            calculation_audit=score_audit,
        )

    def _analyze_all_criteria(
        self,
        normalized_pitch: NormalizedPitch,
        evidence_output: EvidenceExtractionOutput,
    ) -> list[CriterionAnalysis]:
        """Analyze each enabled criterion."""
        analyses = []
        enabled_criteria = self._criteria_config.get_enabled_criteria()

        for criterion in enabled_criteria:
            # Filter evidence citations for this criterion
            criterion_evidence = [
                c for c in evidence_output.citations
                if c.criterion == criterion.name
            ]

            # Analyze this criterion
            result = self._criterion_engine.analyze_criterion(
                normalized_pitch=normalized_pitch,
                criteria_config=self._criteria_config,
                criterion_name=criterion.name,
                evidence_citations=criterion_evidence,
            )

            # Convert to CriterionAnalysis model
            analysis = CriterionAnalysis(
                criterion_name=result.criterion_name,
                proposed_score=result.proposed_score,
                reasoning=result.reasoning,
                evidence_citations=result.evidence_citation_ids,
                strengths=result.strengths,
                weaknesses=result.weaknesses,
                missing_information=result.missing_information,
                uncertainties=result.uncertainties,
                confidence=result.confidence,
            )
            analyses.append(analysis)

        return analyses


def calculate_weighted_score(
    analyses: list[CriterionAnalysis],
    criteria_config: EvaluationCriteriaConfig,
) -> tuple[int, dict[str, int], list[dict[str, Any]]]:
    """Calculate deterministic weighted score from criterion analyses.

    Args:
        analyses: List of criterion analyses with proposed scores
        criteria_config: Evaluation criteria configuration

    Returns:
        Tuple of (weighted_total, criterion_scores_dict, audit_trail)

    Raises:
        ValueError: If validation fails (missing criteria, invalid weights, etc.)
    """
    enabled_criteria = criteria_config.get_enabled_criteria()
    enabled_names = {c.name for c in enabled_criteria}

    # Validate all enabled criteria have analyses
    analysis_names = {a.criterion_name for a in analyses}
    missing = enabled_names - analysis_names
    if missing:
        raise ValueError(f"Missing analyses for criteria: {missing}")

    # Validate weights sum to 1.0
    total_weight = sum(c.weight for c in enabled_criteria)
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(f"Enabled criteria weights must sum to 1.0, got {total_weight}")

    # Calculate weighted score
    criterion_scores = {}
    audit_trail = []
    weighted_sum = 0.0

    for criterion in enabled_criteria:
        analysis = next(a for a in analyses if a.criterion_name == criterion.name)
        score = analysis.proposed_score
        weight = criterion.weight

        # Validate score bounds
        if not 0 <= score <= 100:
            raise ValueError(f"Criterion '{criterion.name}' score out of bounds: {score}")

        weighted_contribution = score * weight
        weighted_sum += weighted_contribution

        criterion_scores[criterion.name] = score
        audit_trail.append({
            "criterion": criterion.name,
            "raw_score": score,
            "weight": weight,
            "weighted_contribution": weighted_contribution,
        })

    # Round to nearest integer
    weighted_total = round(weighted_sum)

    return weighted_total, criterion_scores, audit_trail


def calculate_overall_confidence(
    analyses: list[CriterionAnalysis],
    criteria_config: EvaluationCriteriaConfig,
) -> float:
    """Calculate overall confidence as weighted average of criterion confidences.

    Uses the same weights as the scoring.
    """
    if not criteria_config:
        return 0.0
    enabled_criteria = criteria_config.get_enabled_criteria()
    confidence_sum = 0.0
    total_weight = 0.0

    for criterion in enabled_criteria:
        analysis = next(a for a in analyses if a.criterion_name == criterion.name)
        weight = criterion.weight
        confidence_sum += analysis.confidence * weight
        total_weight += weight

    return confidence_sum / total_weight if total_weight > 0 else 0.0


def calculate_evidence_quality(evidence_citations: list[EvidenceCitation]) -> float:
    """Calculate evidence quality from extracted evidence.

    Simple heuristic based on:
    - Number of citations
    - Verification levels (higher = better)
    - Modality diversity
    """
    if not evidence_citations:
        return 0.0

    # Count citations
    citation_count = len(evidence_citations)

    # Verification level weights
    verification_weights = {
        "independently_verified": 1.0,
        "third_party": 0.8,
        "system_generated": 0.6,
        "self_reported": 0.4,
        "unknown": 0.2,
    }

    # Calculate average verification quality
    verification_scores = []
    modality_set = set()

    for citation in evidence_citations:
        # Verification level score
        vl = citation.verification_level.value if hasattr(citation.verification_level, 'value') else str(citation.verification_level)
        verification_scores.append(verification_weights.get(vl, 0.2))

        # Modality diversity
        for seg in citation.source_segments:
            modality_set.add(seg.source_modality)

    avg_verification = sum(verification_scores) / len(verification_scores)
    modality_diversity = min(len(modality_set) / 4.0, 1.0)  # 4 modalities max

    # Combine factors
    count_factor = min(citation_count / 20.0, 1.0)  # Saturate at 20 citations
    quality = (avg_verification * 0.5) + (modality_diversity * 0.25) + (count_factor * 0.25)

    return round(quality, 3)


def extract_risk_signals(analyses: list[CriterionAnalysis]) -> RiskSignals:
    """Extract deterministic risk signals from criterion analyses.

    Scans weaknesses, missing_information, and uncertainties for
    pattern keywords and categorizes them.
    """
    risk_signals = RiskSignals(
        technical_risk_indicators=[],
        regulatory_risk_indicators=[],
        team_risk_indicators=[],
        market_risk_indicators=[],
        financial_risk_indicators=[],
    )

    # Keyword patterns for each risk category
    technical_keywords = [
        "technical", "architecture", "scalability", "performance", "prototype",
        "feasibility", "implementation", "integration", "api", "platform",
        "code", "development", "engineering", "stack"
    ]
    regulatory_keywords = [
        "regulatory", "compliance", "legal", "certification", "approval",
        "gdpr", "hipaa", "data protection", "privacy", "security",
        "government", "policy", "regulation", "standard"
    ]
    team_keywords = [
        "team", "founder", "experience", "expertise", "hiring", "capability",
        "bandwidth", "capacity", "skill", "background", "track record"
    ]
    market_keywords = [
        "market", "customer", "demand", "traction", "adoption", "competition",
        "go-to-market", "sales", "revenue", "business model", "pricing"
    ]
    financial_keywords = [
        "financial", "funding", "revenue", "cost", "budget", "runway",
        "profitability", "unit economics", "burn rate", "investment"
    ]

    all_text = []
    for analysis in analyses:
        all_text.extend(analysis.weaknesses)
        all_text.extend(analysis.missing_information)
        all_text.extend(analysis.uncertainties)

    combined_text = " ".join(all_text).lower()

    for kw in technical_keywords:
        if kw in combined_text:
            risk_signals.technical_risk_indicators.append(kw)

    for kw in regulatory_keywords:
        if kw in combined_text:
            risk_signals.regulatory_risk_indicators.append(kw)

    for kw in team_keywords:
        if kw in combined_text:
            risk_signals.team_risk_indicators.append(kw)

    for kw in market_keywords:
        if kw in combined_text:
            risk_signals.market_risk_indicators.append(kw)

    for kw in financial_keywords:
        if kw in combined_text:
            risk_signals.financial_risk_indicators.append(kw)

    # Deduplicate
    for attr in [
        "technical_risk_indicators", "regulatory_risk_indicators",
        "team_risk_indicators", "market_risk_indicators", "financial_risk_indicators"
    ]:
        current = getattr(risk_signals, attr)
        setattr(risk_signals, attr, list(dict.fromkeys(current)))

    return risk_signals