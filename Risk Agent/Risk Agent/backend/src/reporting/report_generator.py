from typing import List, Dict, Any
from src.models.startup_profile import StartupProfile
from src.models.research_data import ResearchResults
from src.models.risk_scores import CumulativeRiskAssessment, SimilarCompany, WeightedScore
from src.models.report import FullReport, ExecutiveSummary, MitigationStrategy, DataQuality


class ReportGenerator:
    def generate(
        self,
        profile: StartupProfile,
        research: ResearchResults,
        risk: CumulativeRiskAssessment,
        similar_failures: List[SimilarCompany],
        similar_successes: List[SimilarCompany],
        stats: Dict[str, Any]
    ) -> FullReport:

        score = risk.cumulative_score or risk.overall_score or 0.0
        risk_level = risk.risk_level or "MODERATE"

        # Executive Summary
        exec_summary = ExecutiveSummary(
            cumulative_score=score,
            overall_score=score,
            overall_risk_level=risk_level,
            risk_classification=risk_level,
            top_5_risks=risk.top_risks[:5],
            top_risks=risk.top_risks[:5],
            top_5_strengths=risk.top_strengths[:5],
            key_strengths=risk.top_strengths[:5],
            key_unknowns=risk.key_unknowns,
            critical_warnings=[
                f"High risk identified in: {', '.join(risk.top_risks[:3])}"
            ] if risk.top_risks else [],
            recommendation=self._generate_recommendation(score, risk_level)
        )

        # Build mitigation strategies from top risk categories
        mitigations = []
        for cat_score in risk.category_scores:
            if cat_score.score >= 60:
                mitigations.append(MitigationStrategy(
                    risk_name=cat_score.category,
                    risk_category=cat_score.category,
                    why_it_matters=cat_score.impact or cat_score.impact_description or cat_score.explanation,
                    evidence=cat_score.evidence[:3],
                    recommended_action=cat_score.mitigation or (cat_score.mitigation_suggestions[0] if cat_score.mitigation_suggestions else f"Address {cat_score.category} risk"),
                    strategy=cat_score.mitigation or (cat_score.mitigation_suggestions[0] if cat_score.mitigation_suggestions else f"Address {cat_score.category} risk"),
                    expected_impact="Significant reduction in overall risk score",
                    difficulty="MEDIUM",
                    impact="HIGH"
                ))

        # Collect all citations
        all_citations = []
        for f in research.failures:
            if f.citations:
                all_citations.extend(f.citations)
        for s in research.successes:
            if s.citations:
                all_citations.extend(s.citations)
        if research.industry and research.industry.citations:
            all_citations.extend(research.industry.citations)
        if research.market and research.market.citations:
            all_citations.extend(research.market.citations)
        if research.regulatory and research.regulatory.citations:
            all_citations.extend(research.regulatory.citations)
        if research.competitors and research.competitors.citations:
            all_citations.extend(research.competitors.citations)

        unique_citations = list(set(all_citations))

        # Data quality
        data_quality = DataQuality(
            missing_data=risk.key_unknowns,
            dataset_size=len(research.failures) + len(research.successes),
            assumptions=["Risk weights are industry-standard estimates", "LLM analysis is based on available web data"],
            confidence_levels={cs.category: cs.confidence for cs in risk.category_scores},
            potential_biases=["Selection bias in available failure post-mortems", "Survivorship bias in success analysis"],
            limitations=["Limited to publicly available data", "Historical data may not predict future outcomes"]
        )

        data_quality_note = stats.get('data_quality_notes', 'Analysis based on available data.')

        # Key risk drivers
        key_risk_drivers = [
            f"{cs.category}: {cs.score:.0f}/100 — {cs.explanation[:100]}..."
            for cs in sorted(risk.category_scores, key=lambda x: x.score, reverse=True)[:5]
            if cs.explanation
        ]

        return FullReport(
            executive_summary=exec_summary,
            startup_overview=profile,
            profile=profile,
            risk_assessment=risk,
            research_data=research,
            historical_failures=research.failures,
            successful_benchmarks=research.successes,
            statistical_findings=stats,
            statistical_insights=stats,
            comparable_companies=similar_failures + similar_successes,
            similar_companies=similar_failures + similar_successes,
            score_calculation=risk.weighted_scores,
            key_risk_drivers=key_risk_drivers,
            mitigation_strategies=mitigations,
            data_quality=data_quality,
            data_quality_assessment=data_quality_note,
            sources=[],
            citations=unique_citations
        )

    def _generate_recommendation(self, score: float, risk_level: str) -> str:
        if score >= 80:
            return "VERY HIGH RISK: This startup faces significant challenges across multiple dimensions. Proceed with extreme caution. Address critical risks before seeking investment."
        elif score >= 60:
            return "HIGH RISK: Several major risk factors identified. The startup should prioritize mitigating the top risks before scaling. Consider pivoting or adjusting the business model."
        elif score >= 40:
            return "MODERATE RISK: The startup faces typical startup challenges. Focus on the highest-risk areas and build evidence of product-market fit before aggressive scaling."
        elif score >= 20:
            return "LOW RISK: The startup has a favorable risk profile compared to industry benchmarks. Continue building momentum while monitoring the identified risk factors."
        else:
            return "VERY LOW RISK: Exceptionally favorable risk profile. Rare for an early-stage startup — validate that the assessment has sufficient data."
