"""
Test the API endpoints manually.

This creates a test job and polls for results.
"""

import time
import json
import requests

API_BASE = "http://localhost:8000"


def test_api():
    print("=" * 60)
    print("Testing Triple-TS Speaks API")
    print("=" * 60)
    
    # 1. Create a job
    print("\n1. POST /api/v1/presentations")
    payload = {
        "audio_url": "file://test.wav",
        "video_url": None,
        "language": "en",
        "talk_type": "test",
        "audience_type": "general",
        "requested_metrics": [
            "pace",
            "pause_quality",
            "fillers",
            "intonation",
            "content_structure",
        ],
        "user_metadata": {
            "user_id": "test_user",
            "session_id": "test_session",
        },
    }
    
    response = requests.post(f"{API_BASE}/api/v1/presentations", json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 201:
        print(f"   Error: {response.text}")
        return
    
    data = response.json()
    job_id = data["job_id"]
    print(f"   Job ID: {job_id}")
    print(f"   Status: {data['status']}")
    
    # 2. Poll for completion
    print(f"\n2. GET /api/v1/presentations/{job_id}")
    print("   Polling for completion...")
    
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(2)
        
        response = requests.get(f"{API_BASE}/api/v1/presentations/{job_id}")
        if response.status_code != 200:
            print(f"   Error: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        status = data["status"]
        
        print(f"   [{i+1}/{max_attempts}] Status: {status}")
        
        if status == "done":
            print("   ✓ Job completed!")
            print(f"   Overall score: {data['overall_score']['score_0_100']}/100")
            print(f"   Available metrics: {data['available_metrics']}")
            break
        elif status == "failed":
            print(f"   ✗ Job failed: {data['failure']['message']}")
            return
    
    # 3. Get full results
    print(f"\n3. GET /api/v1/presentations/{job_id}/full")
    response = requests.get(f"{API_BASE}/api/v1/presentations/{job_id}/full")
    
    if response.status_code != 200:
        print(f"   Error: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    print(f"   Metrics computed: {list(data['metrics'].keys())}")
    
    # Print sample metric results
    for metric_name, metric_data in data["metrics"].items():
        if not metric_data["abstained"]:
            score = metric_data["score_0_100"]
            label = metric_data["label"]
            print(f"   - {metric_name}: {score}/100 ({label})")
    
    # 4. Get transcript
    print(f"\n4. GET /api/v1/presentations/{job_id}/transcript")
    response = requests.get(f"{API_BASE}/api/v1/presentations/{job_id}/transcript")
    
    if response.status_code != 200:
        print(f"   Error: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    transcript = data["transcript"]["full_text"]
    print(f"   Transcript: {transcript[:100]}...")
    
    # 5. Delete job
    print(f"\n5. DELETE /api/v1/presentations/{job_id}")
    response = requests.delete(f"{API_BASE}/api/v1/presentations/{job_id}")
    
    if response.status_code == 204:
        print("   ✓ Job deleted")
    else:
        print(f"   Error: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 60)
    print("API test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
