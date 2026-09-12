from typing import List, Dict, Any
from src.models.risk_scores import RiskCategoryScore


class ExplainabilityEngine:
    def build_explanation(self, score: RiskCategoryScore) -> Dict[str, Any]:
        return {
            'category': score.category,
            'overall_score': score.score,
            'confidence': score.confidence,
            'explanation': score.explanation,
            'key_evidence': score.evidence,
            'probability': score.probability or score.probability_estimate,
            'impact': score.impact or score.impact_description,
            'comparable_failures': score.comparable_failures,
            'mitigations': score.mitigation_suggestions if score.mitigation_suggestions else [score.mitigation] if score.mitigation else [],
            'sub_factors': [
                {
                    'name': sf.name,
                    'score': sf.score,
                    'confidence': sf.confidence,
                    'evidence': sf.evidence
                }
                for sf in (score.sub_factors or [])
            ]
        }

    def build_score_calculation_table(self, weighted_scores: list) -> List[Dict[str, Any]]:
        table = []
        for ws in weighted_scores:
            table.append({
                'Category': ws.category,
                'Raw Score': ws.raw_score,
                'Weight': f"{ws.weight:.0%}" if ws.weight <= 1 else f"{ws.weight}%",
                'Weighted Score': round(ws.weighted_score, 2)
            })
        return table
