#!/usr/bin/env python
"""
End-to-end demo runner for the PS Finder discovery agent.
Runs full discovery graph, prints all found opportunities.
"""
import sys
import io
import json
import logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.basicConfig(level=logging.WARNING)  # suppress info noise

from src.graph.discovery_graph import build_discovery_graph

print("=" * 70)
print("  VERIFIED PROBLEM & CHALLENGE DISCOVERY AGENT - DEMO RUN")
print("=" * 70)
print()
print("Building LangGraph discovery graph...")
graph = build_discovery_graph()
print("Running full discovery pipeline (live web + LLM extraction)...")
print()

result = graph.invoke({"query": None})

candidates = result.get("candidates", [])
verified  = result.get("verified_sources", [])
opps      = result.get("final_opportunities", [])
rejected  = result.get("rejected_candidates", [])

print(f"PIPELINE SUMMARY")
print(f"  Candidates discovered : {len(candidates)}")
print(f"  Sources verified      : {len(verified)}")
print(f"  Rejected / skipped    : {len(rejected)}")
print(f"  Opportunities saved   : {len(opps)}")
print()

if opps:
    print("=" * 70)
    print("  VERIFIED OPPORTUNITIES")
    print("=" * 70)
    for i, opp in enumerate(opps, 1):
        print(f"\n[{i}] {opp['title']}")
        print(f"    Organization : {opp.get('organization', {}).get('name', 'N/A')}")
        print(f"    Type         : {opp.get('opportunity_type', 'N/A')}")
        print(f"    Domains      : {', '.join(opp.get('domains', []))}")
        geo = opp.get('geography', {})
        print(f"    Geography    : {geo.get('country', 'N/A')}")
        print(f"    Status       : {opp.get('status', 'N/A')}")
        print(f"    Deadline     : {opp.get('deadline', 'Not specified')}")
        prize = opp.get('prize')
        if prize and prize.get('raw_text'):
            print(f"    Prize        : {prize['raw_text']}")
        print(f"    Verified     : {opp.get('verification_status', 'N/A')}")
        source = opp.get('source', {})
        print(f"    Source URL   : {source.get('url', 'N/A')}")
        ps = opp.get('problem_statement', '')
        print(f"    Problem      : {ps[:200]}{'...' if len(ps) > 200 else ''}")
else:
    print("No verified opportunities discovered in this run.")
    print()
    if rejected:
        print("Rejected candidates (first 3):")
        for r in rejected[:3]:
            cand = r.get("candidate", {})
            print(f"  - {cand.get('title', '?')} : {r.get('reason', '?')}")

print()
print("=" * 70)
print("Run `uvicorn src.main:app --reload` to start the REST API server.")
print("=" * 70)
