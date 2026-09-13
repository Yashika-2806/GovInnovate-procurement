import urllib.request
import json
import time

req = urllib.request.Request(
    'http://localhost:8000/api/analyze',
    data=json.dumps({'problem_statement': 'AI platform predicting hospital patient deterioration'}).encode(),
    headers={'Content-Type': 'application/json'}
)
res = json.loads(urllib.request.urlopen(req).read().decode())
aid = res['analysis_id']
print('Started analysis:', aid)

for i in range(40):
    time.sleep(2)
    s = json.loads(urllib.request.urlopen(f'http://localhost:8000/api/status/{aid}').read().decode())
    print(f"[{i*2}s] Status: {s.get('status')} ({s.get('progress')}%) - {s.get('current_step')}")
    if s.get('status') in ['completed', 'error']:
        break

r = json.loads(urllib.request.urlopen(f'http://localhost:8000/api/results/{aid}').read().decode())
print("\n--- RESULTS VERIFICATION ---")
print('Cumulative Score:', r['executive_summary']['overall_score'])
print('Top Category Scores:', [(cs['category'], cs['score']) for cs in r['risk_assessment']['category_scores']])
print('Historical Comparables:', [(c['company_name'], c['similarity_score'], c['outcome']) for c in r['comparable_companies']])
