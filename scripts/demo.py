"""Run the real HTTP scenario; save actual evidence. Only a local mock may be used."""
import json
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://localhost:18000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url,timeout=60) as client:
        health = client.get("/health")
        health.raise_for_status()
        assert health.json()["marketplace"]=="mock"
        before = client.get("/marketplace").json()
        request = {"request":"Process BMW alternator OEM DEMO-BMW-ALT-001. Check duplicates, compatibility and recommend a price. Prepare a marketplace listing.","entities":{"manufacturer":"BMW","model":"3 Series","year":2019,"condition":"good"}}
        response = client.post("/agent/run",json=request)
        response.raise_for_status()
        run = response.json()
        assert run["status"]=="awaiting_approval",run
        assert len(client.get("/marketplace").json())==len(before)
        aid = run["final_response"]["approval_id"]
        approved = client.post(f"/approvals/{aid}/approve",json={})
        approved.raise_for_status()
        assert len(client.get("/marketplace").json())==len(before)+1
        assert client.post(f"/approvals/{aid}/approve",json={}).status_code==409
        final = client.get(f"/agent/runs/{run['id']}").json()
        trace = client.get(f"/agent/runs/{run['id']}/trace").json()
        assert final["status"]=="completed"
        # Race two HTTP approvals against the actual database service.
        race_run = client.post("/agent/run",json={"request":"Process DEMO-TOYOTA-SNS-001"}).json()
        race_id = race_run["final_response"]["approval_id"]
        def approve_race(_):
            return httpx.post(f"{args.base_url}/approvals/{race_id}/approve",json={},timeout=30).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            race_statuses = sorted(pool.map(approve_race,range(2)))
        assert race_statuses==[200,409],race_statuses
        artifact = {"executed_at":datetime.now(timezone.utc).isoformat(),"health":health.json(),"request":request,"run_before_approval":run,"approval":approved.json(),"run_after_approval":final,"trace":trace,"concurrent_approval_http_statuses":race_statuses}
        (ROOT / "demo/actual_output.json").write_text(json.dumps(artifact,indent=2,ensure_ascii=False),encoding="utf-8")
        r = run["final_response"]
        text = f"""# Actual HTTP demo result

Executed: {artifact['executed_at']}
Base URL: {args.base_url}
Synthetic data; all publication is local mock publication.

- Identified: {r['part']['name']} / {r['part']['oem_number']}
- Matching inventory records before intake: {r['inventory']['record_count']}
- Duplicate candidates: {len(r['duplicates']['candidate_records'])}
- Fitment: {r['compatibility']['status']} against synthetic catalog
- Recommended price: EUR {r['pricing']['suggested_price']:.2f}
- Run stopped at: {run['status']}
- Explicit approval ID: {aid}
- Mock publication: {approved.json()['resolution']['external_id']}
- Final run status: {final['status']}
- Repeated approval: HTTP 409
- Concurrent approval race on a separate draft: {race_statuses}; one execution only
- Tool trace records including approved publication: {len(trace)}

Full actual responses: [actual_output.json](actual_output.json).
Existing local data affects inventory counts, duplicate candidates and pricing on subsequent runs.
"""
        (ROOT / "demo/test_output.md").write_text(text,encoding="utf-8")
        print(text)


if __name__=="__main__":
    main()

