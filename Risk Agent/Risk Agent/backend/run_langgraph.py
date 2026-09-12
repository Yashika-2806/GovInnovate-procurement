import sys
import os
import asyncio
import json
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

from src.utils.llm_client import GeminiClient
from src.utils.search_client import SearchClient
from src.utils.citation_tracker import CitationTracker
from src.agents.orchestrator import RunOrchestrator


def print_banner():
    print("=" * 70, flush=True)
    print("  [>] AI STARTUP RISK EVALUATOR (POWERED BY LANGGRAPH)  ", flush=True)
    print("  Evidence-Driven * Historical Failure Analysis * 12-Factor Scoring", flush=True)
    print("=" * 70, flush=True)


async def main():
    print_banner()

    default_prompt = (
        "We are building an AI-powered platform that helps hospitals predict "
        "patient deterioration using real-time patient data."
    )

    if len(sys.argv) > 1:
        problem_statement = " ".join(sys.argv[1:])
    else:
        print(f"\nNo problem statement provided via arguments.")
        print(f"Using default benchmark startup concept:\n\"{default_prompt}\"\n")
        problem_statement = default_prompt

    print(f"[*] Initializing LangGraph Engine & Research Clients...")
    llm_client = GeminiClient()
    search_client = SearchClient()
    citation_tracker = CitationTracker()
    orchestrator = RunOrchestrator(llm_client, search_client, citation_tracker)

    analysis_id = "langgraph-cli-run"
    print(f"[*] Launching LangGraph Multi-Agent Workflow StateGraph...\n")

    # Step monitor callback
    last_step = ""
    stop_monitor = False
    
    async def monitor_progress():
        nonlocal last_step
        while not stop_monitor:
            status = orchestrator.get_status(analysis_id)
            step = status.get("current_step", "")
            prog = status.get("progress", 0)
            if step and step != last_step:
                print(f"  --> [LangGraph Node] ({prog}%) : {step}")
                last_step = step
            if status.get("status") in ["completed", "error"]:
                break
            await asyncio.sleep(1.0)

    monitor_task = asyncio.create_task(monitor_progress())
    
    try:
        await orchestrator.run(problem_statement, analysis_id)
    except Exception as e:
        print(f"\n[!] Execution error: {e}")
    finally:
        stop_monitor = True
        await monitor_task

    result = orchestrator.get_result(analysis_id)
    if not result:
        print("\n[!] No report produced. Check logs for details.")
        return

    # Display results
    print("\n" + "=" * 70)
    print("  RISK ASSESSMENT SUMMARY")
    print("=" * 70)

    score = result.executive_summary.overall_score or result.executive_summary.cumulative_score
    level = result.executive_summary.overall_risk_level or result.executive_summary.risk_classification
    print(f"\n  Cumulative Startup Risk Score : {score:.1f} / 100")
    print(f"  Risk Classification           : {level}")
    print(f"  Recommendation                : {result.executive_summary.recommendation}\n")

    print("-" * 70)
    print(f"  {'Risk Category':<25} | {'Raw Score':<10} | {'Weight':<8} | {'Weighted Score':<14}")
    print("-" * 70)
    for ws in result.score_calculation:
        print(f"  {ws.category:<25} | {ws.raw_score:<10.1f} | {ws.weight:<8.2f} | {ws.weighted_score:<14.2f}")
    print("-" * 70)

    if result.key_risk_drivers:
        print("\n  TOP RISK DRIVERS:")
        for r in result.key_risk_drivers[:5]:
            print(f"   * {r}")

    if result.comparable_companies:
        print("\n  HISTORICAL COMPARABLE STARTUPS (SIMILARITY RANKING):")
        for comp in result.comparable_companies[:5]:
            outcome_badge = f"[{comp.outcome}]"
            print(f"   * {comp.company_name:<20} {outcome_badge:<12} Similarity: {comp.similarity_score:.0f}%")
            if comp.factors:
                print(f"     Factors: {', '.join(comp.factors)}")
            if comp.key_comparison_points:
                print(f"     Context: {comp.key_comparison_points[0]}")

    if result.citations:
        print("\n  RESEARCH CITATIONS & SOURCES:")
        for c in result.citations[:6]:
            print(f"   * {c}")

    # Write out Markdown report file
    report_filename = "startup_risk_assessment_report.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"# AI Startup Risk Assessment Report\n\n")
        f.write(f"**Startup Problem Statement:**\n> {problem_statement}\n\n")
        f.write(f"**Cumulative Risk Score:** {score:.1f}/100 ({level})\n\n")
        f.write(f"## Executive Summary\n{result.executive_summary.recommendation}\n\n")
        f.write(f"## Top Risks\n")
        for r in result.executive_summary.top_risks:
            f.write(f"- {r}\n")
        f.write(f"\n## Score Breakdown\n\n")
        f.write("| Category | Raw Score | Weight | Weighted Score |\n|---|---|---|---|\n")
        for ws in result.score_calculation:
            f.write(f"| {ws.category} | {ws.raw_score:.1f} | {ws.weight:.2f} | {ws.weighted_score:.2f} |\n")
        f.write(f"\n## Mitigation Strategies\n")
        for m in result.mitigation_strategies:
            f.write(f"### {m.risk_name}\n")
            f.write(f"- **Recommended Action:** {m.recommended_action}\n")
            f.write(f"- **Expected Impact:** {m.expected_impact}\n\n")
        f.write(f"## Sources & Citations\n")
        for c in result.citations:
            f.write(f"- {c}\n")

    print(f"\n[+] Full detailed research report saved to: {os.path.abspath(report_filename)}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
