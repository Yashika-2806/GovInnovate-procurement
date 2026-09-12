"""Quick API test script to verify the system is working end-to-end."""
import sys
import io
import json
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://localhost:8000"

# 1. Health check
print("=" * 60)
print("1. HEALTH CHECK")
print("=" * 60)
r = requests.get(f"{BASE}/health")
print(json.dumps(r.json(), indent=2))

# 2. List all opportunities
print("\n" + "=" * 60)
print("2. ALL DISCOVERED OPPORTUNITIES")
print("=" * 60)
r = requests.get(f"{BASE}/api/opportunities")
data = r.json()
opps = data.get("items", data) if isinstance(data, dict) else data
total = data.get("total", len(opps)) if isinstance(data, dict) else len(opps)
print(f"Total opportunities in database: {total}")
for opp in opps:
    print(f"\n  ID: {opp['id']}")
    print(f"  Title: {opp['title']}")
    org = opp.get('organization', {})
    print(f"  Org: {org.get('name', 'N/A')} ({org.get('type', 'N/A')})")
    print(f"  Type: {opp.get('opportunity_type', 'N/A')}")
    print(f"  Domains: {', '.join(opp.get('domains', []))}")
    print(f"  Status: {opp.get('status', 'N/A')}")
    print(f"  Deadline: {opp.get('deadline', 'N/A')}")
    prize = opp.get('prize')
    if prize and isinstance(prize, dict) and prize.get('amount'):
        print(f"  Prize: {prize.get('currency', 'INR')} {prize['amount']:,.0f}")
    else:
        print(f"  Prize: Not specified")
    src = opp.get('source', {})
    print(f"  Source: {src.get('url', 'N/A')}")
    print(f"  Verification: {opp.get('verification_status', 'N/A')}")

# 3. Test explain on first opportunity (uses Groq now - fast!)
if opps:
    first_id = opps[0]["id"]
    print("\n" + "=" * 60)
    print(f"3. EXPLAIN PROBLEM: {opps[0]['title']}")
    print("=" * 60)
    print("Calling Groq LLM for source-grounded explanation...")
    try:
        r = requests.get(f"{BASE}/api/opportunities/{first_id}/explain", timeout=90)
        if r.status_code == 200:
            explain = r.json()
            print(json.dumps(explain, indent=2, ensure_ascii=False))
        else:
            print(f"Error {r.status_code}: {r.text}")
    except requests.exceptions.Timeout:
        print("Timeout (still > 90s). Check server logs.")

# 4. Test search
print("\n" + "=" * 60)
print("4. SEARCH: 'healthcare'")
print("=" * 60)
r = requests.get(f"{BASE}/api/opportunities/search", params={"q": "healthcare"})
results = r.json()
if isinstance(results, dict):
    items = results.get("items", results.get("results", []))
else:
    items = results
print(f"Results: {len(items)}")
for opp in items:
    if isinstance(opp, dict):
        print(f"  - {opp.get('title', opp)}")

# 5. Test filters
print("\n" + "=" * 60)
print("5. FILTER: status=ACTIVE")
print("=" * 60)
r = requests.get(f"{BASE}/api/opportunities", params={"status": "ACTIVE"})
data = r.json()
items = data.get("items", data) if isinstance(data, dict) else data
print(f"Active opportunities: {len(items)}")
for opp in items:
    print(f"  - [{opp.get('status','?')}] {opp.get('title','?')}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
