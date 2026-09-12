import datetime
from typing import Dict, Any, List
from backend.state import (
    EvaluatorState, EvidenceItem, Milestone, KPI, ScoringWeights,
    MilestoneScore, ContextualPerformanceProfile, AuditLogEntry
)

def get_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def initialize_milestone_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 1: Validate milestone setup, requirements, KPIs, and contractual approval obligations."""
    milestone_dict = state.get("current_milestone", {})
    audit_logs = list(state.get("audit_logs", []))
    
    milestone = Milestone(**milestone_dict) if milestone_dict else None
    if not milestone:
        return {
            "status": "Blocked",
            "recommended_action": "Invalid milestone blueprint provided.",
            "execution_step": "initialize_milestone_node"
        }

    # Contractual obligation check
    contractual_required = milestone.contractual_approval_required
    contractual_granted = milestone.contractual_approval_granted
    
    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "initialize_milestone_node",
        "event": "Milestone Initialized",
        "details": f"Milestone '{milestone.title}' initialized with {len(milestone.requirements)} requirements and {len(milestone.kpis)} KPIs.",
        "uncertainty_alert": None if not contractual_required or contractual_granted else "Contractual approval pending human sign-off."
    }
    audit_logs.append(log_entry)

    if contractual_required and not contractual_granted:
        return {
            "status": "Blocked",
            "human_approval_required": True,
            "human_approval_granted": False,
            "recommended_action": "Milestone creates contractual obligations. Authorized human approval required before evaluation can proceed.",
            "audit_logs": audit_logs,
            "execution_step": "initialize_milestone_node"
        }

    return {
        "status": "In Progress" if state.get("status") == "Pending" else state.get("status", "Under Review"),
        "human_approval_required": contractual_required,
        "human_approval_granted": contractual_granted,
        "audit_logs": audit_logs,
        "execution_step": "initialize_milestone_node"
    }


def ingest_evidence_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 2: Categorize, validate structure, and tag verification trust levels for submitted evidence."""
    raw_evidence_list = state.get("submitted_evidence", [])
    audit_logs = list(state.get("audit_logs", []))
    processed_evidence = []
    
    trust_weights = {
        "Self-reported": 0.50,
        "System-generated": 0.85,
        "Third-party": 0.90,
        "Independently verified": 1.00
    }

    for item_dict in raw_evidence_list:
        try:
            item = EvidenceItem(**item_dict)
        except Exception as e:
            item = EvidenceItem(
                id=item_dict.get("id", "unknown"),
                evidence_type=item_dict.get("evidence_type", "unknown"),
                source=item_dict.get("source", "unknown"),
                timestamp=item_dict.get("timestamp", get_timestamp()),
                verification_level=item_dict.get("verification_level", "Self-reported"),
                relationship_to_milestone=item_dict.get("relationship_to_milestone", "General"),
                relevant_claim=item_dict.get("relevant_claim", ""),
                content_payload=item_dict.get("content_payload", {}),
                is_valid_structure=False,
                uncertainty_score=0.9,
                analysis_notes=f"Structural parsing warning: {str(e)}"
            )
        
        # Base uncertainty derived from verification level
        base_trust = trust_weights.get(item.verification_level, 0.5)
        item.uncertainty_score = round(1.0 - base_trust, 2)
        
        # Check source metadata preservation
        notes = []
        if not item.source:
            notes.append("Missing source attribution.")
            item.uncertainty_score = min(1.0, item.uncertainty_score + 0.2)
        if not item.timestamp:
            item.timestamp = get_timestamp()
            notes.append("Timestamp auto-populated.")
            
        item.analysis_notes = (item.analysis_notes + " " + " ".join(notes)).strip()
        processed_evidence.append(item.model_dump())

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "ingest_evidence_node",
        "event": "Evidence Ingested & Tagged",
        "details": f"Processed {len(processed_evidence)} evidence artifacts with verification trust scores.",
        "uncertainty_alert": f"{sum(1 for e in processed_evidence if e['verification_level'] == 'Self-reported')} items rely purely on self-reporting." if any(e['verification_level'] == 'Self-reported' for e in processed_evidence) else None
    }
    audit_logs.append(log_entry)

    return {
        "submitted_evidence": processed_evidence,
        "audit_logs": audit_logs,
        "execution_step": "ingest_evidence_node"
    }


def evaluate_evidence_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 3: Deep evidence evaluation - assess whether evidence actually proves completion vs dummy uploads."""
    evidence_list = [EvidenceItem(**e) for e in state.get("submitted_evidence", [])]
    milestone_dict = state.get("current_milestone", {})
    milestone = Milestone(**milestone_dict)
    audit_logs = list(state.get("audit_logs", []))

    eval_results = {
        "requirement_fulfillment": {},
        "kpi_fulfillment": {},
        "evidence_quality_score": 0.0,
        "technical_quality_score": 0.0,
        "testing_validation_score": 0.0,
        "documentation_score": 0.0,
        "uncertainty_flags": [],
        "deep_analysis_details": []
    }

    if not evidence_list:
        eval_results["uncertainty_flags"].append("CRITICAL: No evidence submitted for milestone evaluation.")
        log_entry = {
            "timestamp": get_timestamp(),
            "node_name": "evaluate_evidence_node",
            "event": "Deep Analysis Failed",
            "details": "Zero evidence items provided.",
            "uncertainty_alert": "No evidence uploaded."
        }
        audit_logs.append(log_entry)
        return {
            "evidence_analysis": eval_results,
            "status": "Submitted",
            "audit_logs": audit_logs,
            "execution_step": "evaluate_evidence_node"
        }

    # Evaluate requirements based on evidence content payloads
    total_reqs = len(milestone.requirements)
    fulfilled_reqs = 0
    tech_quality_signals = []
    testing_signals = []
    doc_signals = []
    evidence_trust_sum = 0.0

    for req in milestone.requirements:
        # Search for evidence items matching or claiming this requirement
        matching_items = [e for e in evidence_list if req.lower() in e.relationship_to_milestone.lower() or req.lower() in e.relevant_claim.lower() or any(req.lower() in str(v).lower() for v in e.content_payload.values())]
        
        if not matching_items:
            # Fallback to general evidence if available
            matching_items = evidence_list

        req_passed = False
        req_notes = []

        for item in matching_items:
            payload = item.content_payload
            trust_multiplier = 1.0 - item.uncertainty_score

            # Deep evaluation for Software Projects
            if milestone.project_type == "Software":
                # Do NOT just check file existence - check contents/metrics
                commit_count = payload.get("commit_count", 0)
                pr_merged = payload.get("merged_prs_count", 0)
                ci_passed = payload.get("ci_cd_status") == "SUCCESS"
                test_coverage = payload.get("test_coverage_percent", 0.0)
                dummy_repo_flag = payload.get("is_template_repo_only", False) or commit_count < 3

                if dummy_repo_flag:
                    req_notes.append(f"Evidence {item.id} detected as skeletal/dummy template repo with low commit activity ({commit_count} commits).")
                    eval_results["uncertainty_flags"].append(f"Dummy/Skeletal repository upload flagged for Evidence {item.id}.")
                elif ci_passed and test_coverage >= 50.0 and commit_count >= 5:
                    req_passed = True
                    req_notes.append(f"Verified via CI/CD success, {commit_count} commits, {test_coverage}% test coverage.")
                    tech_quality_signals.append(min(100.0, test_coverage * 1.1))
                    testing_signals.append(test_coverage)
                elif commit_count >= 3:
                    req_passed = True
                    req_notes.append(f"Partially verified with {commit_count} commits, test coverage {test_coverage}%.")
                    tech_quality_signals.append(65.0)

                if payload.get("readme_present") and payload.get("api_docs_present"):
                    doc_signals.append(90.0)
                elif payload.get("readme_present"):
                    doc_signals.append(60.0)

            # Deep evaluation for Hardware/Physical Projects
            elif milestone.project_type in ["Hardware", "Hybrid"]:
                telemetry_active = payload.get("telemetry_active", False)
                sample_readings = payload.get("telemetry_readings_count", 0)
                geolocation_verified = payload.get("geolocation_verified", False)
                inspection_grade = payload.get("third_party_inspection_grade", "NONE")
                field_deployment_count = payload.get("field_deployment_count", 0)

                if geolocation_verified and field_deployment_count > 0:
                    req_passed = True
                    req_notes.append(f"Ground verified: {field_deployment_count} field deployments at GPS coordinates.")
                    tech_quality_signals.append(85.0 if inspection_grade in ["A", "PASS"] else 70.0)
                elif telemetry_active and sample_readings > 50:
                    req_passed = True
                    req_notes.append(f"Hardware telemetry active with {sample_readings} sensor readings.")
                    tech_quality_signals.append(80.0)
                elif payload.get("images_count", 0) > 0:
                    req_notes.append("Visual evidence provided but lacks independent sensor telemetry verification.")
                    eval_results["uncertainty_flags"].append(f"Unverified physical photos without telemetry stream for {item.id}.")
                    req_passed = False

            evidence_trust_sum += trust_multiplier

        if req_passed:
            fulfilled_reqs += 1
            eval_results["requirement_fulfillment"][req] = {"status": "Fulfilled", "notes": "; ".join(req_notes)}
        else:
            eval_results["requirement_fulfillment"][req] = {"status": "Unfulfilled", "notes": "; ".join(req_notes) if req_notes else "Insufficient non-trivial evidence."}

    # Evaluate KPIs
    for kpi in milestone.kpis:
        achieved = False
        matching_evidence = [e for e in evidence_list if kpi.name.lower() in str(e.content_payload).lower() or kpi.name.lower() in e.relevant_claim.lower()]
        
        act_val = kpi.actual_value
        if act_val is None and matching_evidence:
            # Extract actual value from payload if reported
            for me in matching_evidence:
                if kpi.name in me.content_payload:
                    try:
                        act_val = float(me.content_payload[kpi.name])
                        break
                    except (ValueError, TypeError):
                        pass
        
        if act_val is not None:
            achieved = act_val >= kpi.target_value
        
        eval_results["kpi_fulfillment"][kpi.name] = {
            "target": kpi.target_value,
            "actual": act_val,
            "unit": kpi.unit,
            "achieved": achieved
        }

    # Aggregate Quality Metrics
    req_ratio = fulfilled_reqs / total_reqs if total_reqs > 0 else 0.0
    avg_trust = (evidence_trust_sum / len(evidence_list)) if evidence_list else 0.0
    
    eval_results["evidence_quality_score"] = round(avg_trust * 100.0, 1)
    eval_results["technical_quality_score"] = round(sum(tech_quality_signals)/len(tech_quality_signals), 1) if tech_quality_signals else round(req_ratio * 75.0, 1)
    eval_results["testing_validation_score"] = round(sum(testing_signals)/len(testing_signals), 1) if testing_signals else round(req_ratio * 70.0, 1)
    eval_results["documentation_score"] = round(sum(doc_signals)/len(doc_signals), 1) if doc_signals else 60.0

    eval_results["deep_analysis_details"].append(f"Evaluated {total_reqs} requirements: {fulfilled_reqs} fulfilled with verified functional criteria.")
    eval_results["deep_analysis_details"].append(f"Average evidence verification confidence: {round(avg_trust * 100, 1)}%.")

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "evaluate_evidence_node",
        "event": "Deep Analysis Complete",
        "details": f"Requirements: {fulfilled_reqs}/{total_reqs} met. Evidence trust factor: {round(avg_trust*100, 1)}%.",
        "uncertainty_alert": "; ".join(eval_results["uncertainty_flags"]) if eval_results["uncertainty_flags"] else None
    }
    audit_logs.append(log_entry)

    return {
        "evidence_analysis": eval_results,
        "status": "Under Review",
        "audit_logs": audit_logs,
        "execution_step": "evaluate_evidence_node"
    }


def analyze_security_and_telemetry_subagent_node(state: EvaluatorState) -> Dict[str, Any]:
    """Specialist Sub-Graph Node: Evaluates Code Security CVEs & IoT Telemetry Stream Anomalies."""
    evidence_list = state.get("submitted_evidence", [])
    milestone_dict = state.get("current_milestone", {})
    audit_logs = list(state.get("audit_logs", []))

    project_type = milestone_dict.get("project_type", "Software")

    sec_audit = {"vulnerability_score": 95.0, "critical_cve_count": 0, "dependency_freshness_score": 90.0, "security_passed": True}
    telem_anomaly = {"telemetry_consistency_percent": 99.1, "gps_spoofing_risk": 0.02, "anomaly_detected": False, "notes": "Telemetry stream consistent."}

    for item in evidence_list:
        payload = item.get("content_payload", {})
        
        # Software Security check
        if project_type == "Software":
            cve_count = payload.get("critical_cves", 0)
            dep_score = payload.get("dependency_freshness", 90.0)
            if cve_count > 0:
                sec_audit["critical_cve_count"] = cve_count
                sec_audit["vulnerability_score"] = max(0.0, 95.0 - (cve_count * 25.0))
                sec_audit["security_passed"] = False
            sec_audit["dependency_freshness_score"] = dep_score

        # Hardware/IoT Telemetry Anomaly & GPS Spoofing check
        elif project_type in ["Hardware", "Hybrid"]:
            gps_verified = payload.get("geolocation_verified", False)
            readings = payload.get("telemetry_readings_count", 0)
            is_spoofed = payload.get("gps_spoofing_flag", False)

            if is_spoofed or (readings > 0 and not gps_verified):
                telem_anomaly["gps_spoofing_risk"] = 0.85
                telem_anomaly["anomaly_detected"] = True
                telem_anomaly["notes"] = "HIGH RISK: Potential GPS spoofing or unverified location stream detected."
                telem_anomaly["telemetry_consistency_percent"] = 45.0
            elif readings > 0:
                telem_anomaly["telemetry_consistency_percent"] = min(100.0, 95.0 + (readings * 0.05))

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "analyze_security_and_telemetry_subagent_node",
        "event": "Security & Telemetry Audit Completed",
        "details": f"Software Security Passed: {sec_audit['security_passed']}. IoT Anomaly Detected: {telem_anomaly['anomaly_detected']}.",
        "uncertainty_alert": telem_anomaly["notes"] if telem_anomaly["anomaly_detected"] else None
    }
    audit_logs.append(log_entry)

    return {
        "security_audit": sec_audit,
        "telemetry_anomaly": telem_anomaly,
        "audit_logs": audit_logs,
        "execution_step": "analyze_security_and_telemetry_subagent_node"
    }


def calculate_escrow_disbursement_node(state: EvaluatorState) -> Dict[str, Any]:
    """Specialist Sub-Graph Node: Computes Escrow Tranche Payouts, Penalties, and Financial Authorizations."""
    score_dict = state.get("milestone_score", {})
    milestone_dict = state.get("current_milestone", {})
    audit_logs = list(state.get("audit_logs", []))

    score = MilestoneScore(**score_dict) if score_dict else MilestoneScore()
    passed = score.passed

    tranche_base = float(milestone_dict.get("escrow_tranche_usd", 50000.0))
    penalty = 0.0

    # Calculate penalty if score is low or evidence trust was poor
    if passed:
        if score.evidence_quality_score < 70.0:
            penalty = tranche_base * 0.05  # 5% deduction for low evidence quality
        net_payout = tranche_base - penalty
        escrow_status = "Approved"
        notes = f"Escrow tranche of ${net_payout:,.2f} authorized for release." + (f" (${penalty:,.2f} penalty applied for low evidence quality)." if penalty > 0 else "")
    else:
        penalty = 0.0
        net_payout = 0.0
        escrow_status = "Withheld"
        notes = "Escrow disbursement withheld due to unfulfilled milestone criteria."

    disbursement = {
        "tranche_amount_usd": tranche_base,
        "penalty_deduction_usd": penalty,
        "net_payout_usd": net_payout,
        "escrow_status": escrow_status,
        "disbursement_notes": notes
    }

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "calculate_escrow_disbursement_node",
        "event": "Escrow Disbursement Calculated",
        "details": f"Escrow Status: {escrow_status}. Net Payout: ${net_payout:,.2f} USD.",
        "uncertainty_alert": None
    }
    audit_logs.append(log_entry)

    return {
        "escrow_disbursement": disbursement,
        "audit_logs": audit_logs,
        "execution_step": "calculate_escrow_disbursement_node"
    }



def calculate_milestone_score_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 5: Compute weighted score across 8 criteria and test against pass threshold."""
    analysis = state.get("evidence_analysis", {})
    weights_dict = state.get("scoring_weights", {})
    milestone_dict = state.get("current_milestone", {})
    audit_logs = list(state.get("audit_logs", []))

    weights = ScoringWeights(**weights_dict) if weights_dict else ScoringWeights()
    milestone = Milestone(**milestone_dict)

    # 1. Requirement Completion Score
    req_fulfill = analysis.get("requirement_fulfillment", {})
    total_reqs = len(req_fulfill)
    fulfilled_count = sum(1 for v in req_fulfill.values() if v.get("status") == "Fulfilled")
    req_completion_score = (fulfilled_count / total_reqs * 100.0) if total_reqs > 0 else 0.0

    # 2. KPI Achievement Score
    kpi_fulfill = analysis.get("kpi_fulfillment", {})
    total_kpis = len(kpi_fulfill)
    achieved_kpis = sum(1 for v in kpi_fulfill.values() if v.get("achieved", False))
    kpi_score = (achieved_kpis / total_kpis * 100.0) if total_kpis > 0 else 100.0

    # 3. Technical Quality
    tech_quality_score = float(analysis.get("technical_quality_score", 70.0))

    # 4. Evidence Quality
    evidence_quality_score = float(analysis.get("evidence_quality_score", 50.0))

    # 5. Testing & Validation
    testing_score = float(analysis.get("testing_validation_score", 60.0))

    # 6. Documentation
    doc_score = float(analysis.get("documentation_score", 60.0))

    # 7. Practicality
    practicality_score = 85.0 if req_completion_score >= 80.0 else 60.0

    # 8. Delivery Timeliness
    delivery_timeliness_score = 95.0

    # Normalize weights so they always sum to 1.0 (prevent score inflation)
    raw_weights = [
        weights.requirement_completion,
        weights.kpi_achievement,
        weights.technical_quality,
        weights.evidence_quality,
        weights.testing_validation,
        weights.documentation,
        weights.practicality,
        weights.delivery_timeliness
    ]
    total_weight = sum(raw_weights)
    if total_weight > 0:
        norm = [w / total_weight for w in raw_weights]
    else:
        norm = [1/8] * 8

    scores = [
        req_completion_score,
        kpi_score,
        tech_quality_score,
        evidence_quality_score,
        testing_score,
        doc_score,
        practicality_score,
        delivery_timeliness_score
    ]

    total_weighted = sum(s * w for s, w in zip(scores, norm))
    total_weighted = min(100.0, round(total_weighted, 2))
    passed = total_weighted >= weights.pass_threshold

    score_result = MilestoneScore(
        requirement_completion_score=round(req_completion_score, 1),
        kpi_achievement_score=round(kpi_score, 1),
        technical_quality_score=round(tech_quality_score, 1),
        evidence_quality_score=round(evidence_quality_score, 1),
        testing_validation_score=round(testing_score, 1),
        documentation_score=round(doc_score, 1),
        practicality_score=round(practicality_score, 1),
        delivery_timeliness_score=round(delivery_timeliness_score, 1),
        total_weighted_score=total_weighted,
        passed=passed
    )

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "calculate_milestone_score_node",
        "event": "Milestone Score Calculated",
        "details": f"Total Weighted Score: {total_weighted}/100. Pass Threshold: {weights.pass_threshold}. Outcome: {'PASS' if passed else 'FAIL'}.",
        "uncertainty_alert": None
    }
    audit_logs.append(log_entry)

    score_dict = score_result.model_dump()
    score_dict["pass_threshold"] = weights.pass_threshold
    score_dict["criterion_weights"] = {
        "requirement_completion": round(norm[0], 4),
        "kpi_achievement":        round(norm[1], 4),
        "technical_quality":      round(norm[2], 4),
        "evidence_quality":       round(norm[3], 4),
        "testing_validation":     round(norm[4], 4),
        "documentation":          round(norm[5], 4),
        "practicality":           round(norm[6], 4),
        "delivery_timeliness":    round(norm[7], 4),
    }
    return {
        "milestone_score": score_dict,
        "audit_logs": audit_logs,
        "execution_step": "calculate_milestone_score_node"
    }


def generate_justification_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 5: Generate explicit line-by-line point award and deduction justifications."""
    score_dict = state.get("milestone_score", {})
    weights_dict = state.get("scoring_weights", {})
    analysis = state.get("evidence_analysis", {})
    audit_logs = list(state.get("audit_logs", []))

    score = MilestoneScore(**score_dict)
    weights = ScoringWeights(**weights_dict) if weights_dict else ScoringWeights()

    justification_lines = []
    deductions = []
    awards = []

    # Requirement Completion
    max_req_pts = weights.requirement_completion * 100
    awarded_req_pts = (score.requirement_completion_score / 100.0) * max_req_pts
    awards.append(f"Requirement Completion: Awarded {round(awarded_req_pts, 2)} / {max_req_pts} pts ({score.requirement_completion_score}% requirements fulfilled).")
    if score.requirement_completion_score < 100.0:
        deductions.append(f"Deducted {round(max_req_pts - awarded_req_pts, 2)} pts due to unfulfilled functional requirements.")

    # KPI Achievement
    max_kpi_pts = weights.kpi_achievement * 100
    awarded_kpi_pts = (score.kpi_achievement_score / 100.0) * max_kpi_pts
    awards.append(f"KPI Achievement: Awarded {round(awarded_kpi_pts, 2)} / {max_kpi_pts} pts ({score.kpi_achievement_score}% KPIs met).")
    if score.kpi_achievement_score < 100.0:
        deductions.append(f"Deducted {round(max_kpi_pts - awarded_kpi_pts, 2)} pts for missed target KPI metrics.")

    # Evidence Quality & Verification
    max_ev_pts = weights.evidence_quality * 100
    awarded_ev_pts = (score.evidence_quality_score / 100.0) * max_ev_pts
    awards.append(f"Evidence Quality: Awarded {round(awarded_ev_pts, 2)} / {max_ev_pts} pts (Average verification trust level: {score.evidence_quality_score}%).")
    if score.evidence_quality_score < 80.0:
        deductions.append(f"Deducted {round(max_ev_pts - awarded_ev_pts, 2)} pts because evidence relied heavily on unverified or self-reported uploads.")

    # Technical & Testing Quality
    max_tech_pts = weights.technical_quality * 100
    awarded_tech_pts = (score.technical_quality_score / 100.0) * max_tech_pts
    awards.append(f"Technical Quality: Awarded {round(awarded_tech_pts, 2)} / {max_tech_pts} pts.")

    flags = analysis.get("uncertainty_flags", [])
    
    summary_text = (
        f"Milestone evaluated with a final score of {score.total_weighted_score} / 100. "
        f"Pass Threshold is set to {weights.pass_threshold}. "
        f"Result: {'PASSED' if score.passed else 'REQUIRES REMEDIATION / FAILED'}."
    )

    report = {
        "summary": summary_text,
        "awards": awards,
        "deductions": deductions,
        "uncertainty_warnings": flags,
        "generated_at": get_timestamp()
    }

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "generate_justification_node",
        "event": "Point Justification Generated",
        "details": f"Synthesized {len(awards)} award notes and {len(deductions)} deduction notes.",
        "uncertainty_alert": "; ".join(flags) if flags else None
    }
    audit_logs.append(log_entry)

    return {
        "justification_report": report,
        "audit_logs": audit_logs,
        "execution_step": "generate_justification_node"
    }


def update_startup_performance_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 6: Dynamic Startup Performance update - recalculate contextual execution vector & domain rankings."""
    profile_dict = state.get("startup_profile", {})
    score_dict = state.get("milestone_score", {})
    analysis = state.get("evidence_analysis", {})
    audit_logs = list(state.get("audit_logs", []))

    profile = ContextualPerformanceProfile(**profile_dict) if profile_dict else ContextualPerformanceProfile(
        startup_id="startup-01",
        startup_name="AeroSense Robotics",
        primary_domain="Industrial IoT",
        initial_pitch_score=88.0,
        demonstrated_execution_score=0.0
    )

    score = MilestoneScore(**score_dict)
    
    # Calculate updated demonstrated execution score (strictly based on actual milestone results)
    new_completed = profile.historical_milestones_completed + (1 if score.passed else 0)
    new_failed = profile.historical_milestones_failed + (0 if score.passed else 1)
    total_evals = new_completed + new_failed
    
    # Weighted average of demonstrated scores
    prev_exec = profile.demonstrated_execution_score
    if total_evals == 1:
        updated_exec_score = score.total_weighted_score
    else:
        updated_exec_score = round((prev_exec * (total_evals - 1) + score.total_weighted_score) / total_evals, 1)

    profile.historical_milestones_completed = new_completed
    profile.historical_milestones_failed = new_failed
    profile.demonstrated_execution_score = updated_exec_score

    # Contextual Domain Vector Ranking Update
    # Update domain-specific competence based on current milestone performance
    domain = profile.primary_domain
    current_domain_vec = dict(profile.domain_relevance_vector)
    current_domain_score = current_domain_vec.get(domain, profile.initial_pitch_score)
    
    # Recalculate domain score: Demonstrated execution weighs 70%, Pitch weighs 30%
    new_domain_score = round(0.30 * profile.initial_pitch_score + 0.70 * updated_exec_score, 1)
    current_domain_vec[domain] = new_domain_score
    
    # Add adjacent contextual domain scores with domain-transfer penalty
    if domain == "Industrial IoT":
        current_domain_vec["Hardware/Sensors"] = round(new_domain_score * 0.95, 1)
        current_domain_vec["Robotics"] = round(new_domain_score * 0.90, 1)
        current_domain_vec["Healthcare AI"] = round(new_domain_score * 0.60, 1)  # Weaker in non-core domain
    elif domain == "Healthcare AI":
        current_domain_vec["Medical Devices"] = round(new_domain_score * 0.92, 1)
        current_domain_vec["Diagnostics"] = round(new_domain_score * 0.96, 1)
        current_domain_vec["Industrial IoT"] = round(new_domain_score * 0.55, 1)

    profile.domain_relevance_vector = current_domain_vec

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "update_startup_performance_node",
        "event": "Startup Performance Profile Updated",
        "details": f"Updated Demonstrated Execution Score to {updated_exec_score} (Pitch Capability: {profile.initial_pitch_score}). Contextual domain vector updated for {domain}.",
        "uncertainty_alert": None
    }
    audit_logs.append(log_entry)

    return {
        "startup_profile": profile.model_dump(),
        "audit_logs": audit_logs,
        "execution_step": "update_startup_performance_node"
    }


def determine_next_action_node(state: EvaluatorState) -> Dict[str, Any]:
    """Node 7: Determine final milestone status and recommend next action."""
    score_dict = state.get("milestone_score", {})
    analysis = state.get("evidence_analysis", {})
    audit_logs = list(state.get("audit_logs", []))
    human_approval_required = state.get("human_approval_required", False)
    human_approval_granted = state.get("human_approval_granted", False)

    score = MilestoneScore(**score_dict)
    flags = analysis.get("uncertainty_flags", [])

    if human_approval_required and not human_approval_granted:
        final_status = "Blocked"
        next_action = "Awaiting authorized human approval for contractual obligation sign-off."
    elif not score.passed:
        if flags or score.evidence_quality_score < 60.0:
            final_status = "Requires Remediation"
            next_action = "Startup must submit higher-confidence independent/system-generated evidence for unfulfilled requirements within 14 days."
        else:
            final_status = "Failed"
            next_action = "Milestone evaluation failed to meet pass threshold. Escalate to problem owner for review."
    else:
        if flags:
            final_status = "Passed"
            next_action = "Milestone Passed with minor evidence quality warnings. Release milestone tranche payment and proceed to next milestone."
        else:
            final_status = "Passed"
            next_action = "Milestone Passed cleanly with verified evidence. Authorize escrow disbursement and proceed to next milestone."

    log_entry = {
        "timestamp": get_timestamp(),
        "node_name": "determine_next_action_node",
        "event": "Final Decision Rendered",
        "details": f"Final Status: {final_status}. Recommended Action: {next_action}",
        "uncertainty_alert": None
    }
    audit_logs.append(log_entry)

    return {
        "status": final_status,
        "recommended_action": next_action,
        "audit_logs": audit_logs,
        "execution_step": "determine_next_action_node"
    }
