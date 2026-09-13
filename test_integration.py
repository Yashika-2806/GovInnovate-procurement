#!/usr/bin/env python
"""
END-TO-END WORKFLOW TEST
Tests real multi-agent integration through HTTP.
"""

import sys
import httpx
import asyncio
import json
from pathlib import Path

root = Path(__file__).parent

async def test_workflow():
    """Test complete workflow."""
    print("=" * 80)
    print("GOVINNOVATE END-TO-END WORKFLOW TEST")
    print("=" * 80)
    print()

    # Port check
    print("PORT STATUS:")
    ports = {
        8000: "Orchestrator",
        8001: "Pitch Evaluator",
        8002: "PS Finder",
        8003: "Risk Detector",
        8004: "Evaluator",
    }

    async with httpx.AsyncClient() as client:
        for port, name in ports.items():
            try:
                r = await client.get(f"http://localhost:{port}/", timeout=1)
                print(f"  [{r.status_code:3d}] {name:20} port {port}")
            except Exception as e:
                print(f"  [   ] {name:20} port {port} - {type(e).__name__}")

        print()
        print("=" * 80)
        print("TEST 1: Create Workflow")
        print("=" * 80)

        opp = {
            "id": "test-opp-1",
            "title": "Energy Infrastructure",
            "description": "Renewable energy pilot program",
            "organization": "Ministry of Energy",
            "status": "active"
        }

        try:
            r = await client.post("http://localhost:8000/api/workflows", json=opp, timeout=5)
            print(f"Status: {r.status_code}")
            if r.status_code == 201:
                wf = r.json()
                wf_id = wf["workflow_id"]
                print(f"Workflow ID: {wf_id}")
                print(f"State: {wf['state']}")

                print()
                print("=" * 80)
                print("TEST 2: Pitch Evaluator Agent")
                print("=" * 80)

                # Test pitch evaluator directly
                pitch_req = {
                    "id": "pitch-1",
                    "startup_id": "startup-1",
                    "opportunity_id": opp["id"],
                    "metadata": {"title": "Solar Solution"}
                }
                try:
                    r2 = await client.post("http://localhost:8001/evaluate", json=pitch_req, timeout=5)
                    print(f"Direct call status: {r2.status_code}")
                    if r2.status_code == 200:
                        print(f"Result: {r2.json()}")
                    else:
                        print(f"Error: {r2.text[:200]}")
                except Exception as e:
                    print(f"Failed: {e}")

                print()
                print("=" * 80)
                print("TEST 3: Risk Detector Agent")
                print("=" * 80)

                # Test risk detector
                risk_req = {"problem_statement": opp["description"]}
                try:
                    r3 = await client.post("http://localhost:8003/api/analyze", json=risk_req, timeout=5)
                    print(f"Direct call status: {r3.status_code}")
                    if r3.status_code in [200, 202]:
                        data = r3.json()
                        print(f"Response: {json.dumps(data, indent=2)[:300]}")
                    else:
                        print(f"Error: {r3.text[:200]}")
                except Exception as e:
                    print(f"Failed: {e}")

                print()
                print("=" * 80)
                print("TEST 4: PS Finder Agent")
                print("=" * 80)

                # Test PS finder
                try:
                    r4 = await client.get("http://localhost:8002/api/opportunities?q=energy&page_size=1", timeout=5)
                    print(f"Direct call status: {r4.status_code}")
                    if r4.status_code == 200:
                        data = r4.json()
                        print(f"Found {data.get('total', 0)} opportunities")
                    else:
                        print(f"Error: {r4.text[:200]}")
                except Exception as e:
                    print(f"Failed: {e}")

                print()
                print("=" * 80)
                print("TEST 5: Evaluator Agent")
                print("=" * 80)

                # Test evaluator
                eval_req = {
                    "state": {
                        "startup_profile": {"startup_id": "startup-1"},
                        "current_milestone": {"milestone_id": "m1"},
                    }
                }
                try:
                    r5 = await client.post("http://localhost:8004/api/evaluate", json=eval_req, timeout=5)
                    print(f"Direct call status: {r5.status_code}")
                    if r5.status_code == 200:
                        data = r5.json()
                        print(f"Result keys: {list(data.keys())}")
                    else:
                        print(f"Error: {r5.text[:200]}")
                except Exception as e:
                    print(f"Failed: {e}")

            else:
                print(f"Error: {r.text[:200]}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
