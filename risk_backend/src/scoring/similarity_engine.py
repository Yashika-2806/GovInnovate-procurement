from typing import List, Dict, Any, Union, Optional
from src.models.startup_profile import StartupProfile
from src.models.research_data import FailedStartup, SuccessfulStartup, FailureCause
from src.models.risk_scores import SimilarCompany


CURATED_BENCHMARKS = [
    FailedStartup(
        company_name="Olive AI",
        industry="Healthcare Technology",
        funding_raised="$852M",
        primary_cause="EXCESSIVE_BURN",
        failure_causes=[FailureCause.EXCESSIVE_BURN, FailureCause.LACK_OF_PMF, FailureCause.POOR_EXECUTION],
        failure_narrative="Olive attempted to automate hospital administrative workflows using AI. It scaled sales prematurely before core AI products were reliable, leading to massive burn rate and hospital customer dissatisfaction.",
        citations=["https://www.healthcaredive.com/news/olive-ai-shuts-down/698455"]
    ),
    FailedStartup(
        company_name="Theranos",
        industry="Healthcare",
        funding_raised="$700M",
        primary_cause="REGULATORY",
        failure_causes=[FailureCause.REGULATORY, FailureCause.LEGAL, FailureCause.FRAUD],
        failure_narrative="Theranos promised revolutionary diagnostic blood testing but avoided peer review and regulatory scrutiny. The technology failed validation, leading to federal regulatory bans and total collapse.",
        citations=["https://en.wikipedia.org/wiki/Theranos"]
    ),
    FailedStartup(
        company_name="Fast",
        industry="Fintech",
        funding_raised="$125M",
        primary_cause="CASH_FLOW",
        failure_causes=[FailureCause.CASH_FLOW, FailureCause.EXCESSIVE_BURN, FailureCause.COMPETITION],
        failure_narrative="One-click checkout startup burned $10M/month with only $600k in annual revenue. Faced intense competition from Stripe, PayPal, and Apple Pay.",
        citations=["https://techcrunch.com/2022/04/05/fast-is-shutting-down/"]
    ),
    FailedStartup(
        company_name="InVision",
        industry="B2B SaaS",
        funding_raised="$350M",
        primary_cause="COMPETITION",
        failure_causes=[FailureCause.COMPETITION, FailureCause.TECH_FAILURE],
        failure_narrative="Prototyping platform was overtaken by Figma's collaborative, browser-native product architecture and failed to pivot in time.",
        citations=["https://techcrunch.com/2024/01/11/invision-shutting-down/"]
    ),
    FailedStartup(
        company_name="Quibi",
        industry="Consumer Social",
        funding_raised="$1.75B",
        primary_cause="LACK_OF_PMF",
        failure_causes=[FailureCause.LACK_OF_PMF, FailureCause.HIGH_CAC, FailureCause.MARKET_TOO_SMALL],
        failure_narrative="Short-form mobile video subscription failed to achieve product-market fit against free social platforms like TikTok and YouTube.",
        citations=["https://www.bbc.com/news/business-54637048"]
    ),
    SuccessfulStartup(
        company_name="Innovaccer",
        industry="Healthcare Technology",
        funding_raised="$379M",
        current_valuation="$3.2B",
        success_factors=["Unified data activation platform across hospital EHRs", "Direct ROI demonstration for value-based care"],
        key_differentiators=["Interoperability across disparate health IT systems", "High customer retention among major health networks"],
        citations=["https://innovaccer.com/"]
    ),
    SuccessfulStartup(
        company_name="Stripe",
        industry="Fintech",
        funding_raised="$2.2B",
        current_valuation="$65B",
        success_factors=["Developer-first API approach", "Frictionless international payments"],
        key_differentiators=["Superior developer experience", "Comprehensive financial infrastructure"],
        citations=["https://stripe.com/"]
    ),
    SuccessfulStartup(
        company_name="Datadog",
        industry="B2B SaaS",
        funding_raised="$148M",
        current_valuation="$40B",
        success_factors=["Unified observability across infrastructure and applications", "Strong land-and-expand sales motion"],
        key_differentiators=["Seamless cloud integrations", "High Net Expansion Rate"],
        citations=["https://www.datadoghq.com/"]
    )
]


class SimilarityEngine:
    def compute_similarity(self, profile: StartupProfile, company: Union[FailedStartup, SuccessfulStartup]) -> SimilarCompany:
        score = 0.25
        factors = ["Enterprise software baseline"]

        p_ind = (profile.industry.value or "").lower() if profile.industry else ""
        p_sub = (profile.sub_industry.value or "").lower() if profile.sub_industry else ""
        p_tc = (profile.target_customers.value or "").lower() if profile.target_customers else ""
        p_tech = (profile.technology.value or "").lower() if profile.technology else ""

        c_ind = (company.industry or "").lower()
        c_name = getattr(company, 'company_name', 'Unknown')
        c_desc = (company.product_description or getattr(company, 'failure_narrative', '') or '').lower()

        # Vertical & Industry matching
        if p_ind and c_ind:
            if p_ind == c_ind:
                score += 0.40
                factors.append("Exact industry match")
            elif any(word in c_ind for word in p_ind.split() if len(word) > 3):
                score += 0.30
                factors.append(f"Related vertical ({company.industry})")
        elif any(k in (c_ind + " " + c_name.lower()) for k in ["health", "hospital", "patient", "clinical"]) and any(k in (p_ind + " " + p_tc) for k in ["health", "hospital", "patient", "clinical"]):
            score += 0.40
            factors.append("Direct Healthcare alignment")
        elif any(k in c_ind for k in ["saas", "tech", "ai", "fintech"]) and any(k in p_ind for k in ["saas", "tech", "ai", "fintech"]):
            score += 0.25
            factors.append("Enterprise software sector overlap")

        # Customer & Workflow matching
        if any(term in (p_tc + " " + p_sub) for term in ["hospital", "clinical", "health", "doctor"]):
            if any(term in (c_desc + " " + c_ind) for term in ["hospital", "clinical", "ehr", "health", "administrative"]):
                score += 0.20
                factors.append("Hospital administrative / Clinical workflow overlap")

        # Technology stack matching
        if any(tech in (p_tech + " " + p_sub) for tech in ["ai", "machine learning", "predictive", "analytics", "data"]):
            if any(tech in c_desc for tech in ["ai", "machine learning", "data", "analytics", "predictive"]):
                score += 0.15
                factors.append("Predictive AI / Machine learning core")

        # Negative penalty for radically different sectors
        if "consumer" in c_ind and "hospital" in (p_tc + " " + p_ind):
            score = max(0.18, score - 0.15)

        score = min(0.95, max(0.18, score))
        similarity_pct = round(score * 100, 0)

        is_failed = isinstance(company, FailedStartup) or hasattr(company, 'failure_causes')
        outcome = "FAILED" if is_failed else "SUCCEEDED"

        comparison_points = []
        if is_failed:
            cause = getattr(company, 'primary_cause', 'Market conditions')
            narrative = getattr(company, 'failure_narrative', '')
            raised = getattr(company, 'funding_raised', None)
            comparison_points.append(f"Primary Failure Cause: {cause}")
            if raised:
                comparison_points.append(f"Capital Lost: {raised}")
            if narrative:
                comparison_points.append(f"Post-Mortem: {narrative[:120]}...")
        else:
            factors_list = getattr(company, 'success_factors', [])
            val = getattr(company, 'current_valuation', None)
            if factors_list:
                comparison_points.append(f"Key Success Driver: {factors_list[0]}")
            if val:
                comparison_points.append(f"Valuation Scale: {val}")

        return SimilarCompany(
            company_name=c_name,
            similarity_score=similarity_pct,
            similarity_factors=factors,
            factors=factors,
            outcome=outcome,
            key_comparison_points=comparison_points
        )

    def rank_similar_companies(self, profile: StartupProfile, companies: list, outcome_filter: Optional[str] = None) -> List[SimilarCompany]:
        combined = list(companies or [])
        combined_names = {getattr(c, 'company_name', '').lower() for c in combined}

        for bench in CURATED_BENCHMARKS:
            if bench.company_name.lower() not in combined_names:
                combined.append(bench)

        similarities = []
        for company in combined:
            try:
                sim = self.compute_similarity(profile, company)
                if outcome_filter:
                    if sim.outcome.upper() != outcome_filter.upper():
                        continue
                similarities.append(sim)
            except Exception as e:
                print(f"Error computing similarity for {company}: {e}")
                continue

        # Sort descending by similarity score
        return sorted(similarities, key=lambda x: x.similarity_score, reverse=True)[:5]
